import base64
import json
from urllib.parse import quote
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException, Request as FastAPIRequest, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin
from app.config import Settings, get_settings
from app.database import get_db
from app.models import Order, PaymentStatus, PaymentTransaction, User
from app.notifications import notify_order_customer
from app.order_ops import refund_totals_by_refund_id
from app.payment_utils import (
    verify_razorpay_payment_signature,
    verify_razorpay_webhook_signature,
)
from app.schemas import (
    RazorpayOrderCreate,
    RazorpayOrderOut,
    RazorpayRefundCreate,
    RazorpayRefundOut,
    RazorpayRefundStatusOut,
    RazorpayWebhookOut,
    RazorpayVerifyOut,
    RazorpayVerifyRequest,
    PaymentTransactionOut,
)

router = APIRouter(prefix="/payments", tags=["payments"])


def rupees_to_paise(value: float) -> int:
    return round(value * 100)


def paise_to_rupees(value: int) -> float:
    return value / 100


def require_razorpay_settings(settings: Settings) -> None:
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Razorpay credentials are not configured",
        )


def enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def razorpay_auth_header(settings: Settings) -> str:
    credentials = f"{settings.razorpay_key_id}:{settings.razorpay_key_secret}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
    return f"Basic {encoded}"


def record_payment_transaction(
    db: Session,
    *,
    event_type: str,
    status_value: str,
    verified: bool,
    provider_order_id: str | None = None,
    provider_payment_id: str | None = None,
    provider_refund_id: str | None = None,
    order: Order | None = None,
    user: User | None = None,
    amount_paise: int = 0,
    currency: str = "INR",
    signature: str | None = None,
    raw_payload: dict | None = None,
) -> PaymentTransaction:
    transaction = PaymentTransaction(
        order_id=order.id if order else None,
        user_id=user.id if user else order.user_id if order else None,
        provider="razorpay",
        provider_order_id=provider_order_id,
        provider_payment_id=provider_payment_id,
        provider_refund_id=provider_refund_id,
        event_type=event_type,
        status=status_value,
        amount_paise=amount_paise,
        currency=currency,
        verified=verified,
        signature=signature,
        raw_payload=raw_payload or {},
    )
    db.add(transaction)
    return transaction


def find_order_for_payment_event(
    db: Session,
    *,
    provider_order_id: str | None,
    provider_payment_id: str | None,
) -> Order | None:
    transaction = None
    if provider_payment_id:
        transaction = db.scalar(
            select(PaymentTransaction)
            .where(
                PaymentTransaction.provider == "razorpay",
                PaymentTransaction.provider_payment_id == provider_payment_id,
                PaymentTransaction.order_id.is_not(None),
            )
            .order_by(PaymentTransaction.created_at.desc(), PaymentTransaction.id.desc())
        )
    if transaction is None and provider_order_id:
        transaction = db.scalar(
            select(PaymentTransaction)
            .where(
                PaymentTransaction.provider == "razorpay",
                PaymentTransaction.provider_order_id == provider_order_id,
                PaymentTransaction.order_id.is_not(None),
            )
            .order_by(PaymentTransaction.created_at.desc(), PaymentTransaction.id.desc())
        )
    return transaction.order if transaction else None


def apply_webhook_payment_status(order: Order | None, event_type: str) -> str | None:
    if order is None:
        return None
    if event_type in {"payment.captured", "payment.authorized"}:
        order.payment_status = PaymentStatus.PAID
    elif event_type == "payment.failed":
        order.payment_status = PaymentStatus.FAILED
    elif event_type.startswith("refund."):
        order.payment_status = PaymentStatus.REFUNDED
    return enum_value(order.payment_status)


def latest_razorpay_payment_transaction(order_id: int, db: Session) -> PaymentTransaction | None:
    return db.scalar(
        select(PaymentTransaction)
        .where(
            PaymentTransaction.order_id == order_id,
            PaymentTransaction.provider == "razorpay",
            PaymentTransaction.provider_payment_id.is_not(None),
        )
        .order_by(PaymentTransaction.created_at.desc(), PaymentTransaction.id.desc())
    )


def refunded_amount_paise(order_id: int, db: Session) -> int:
    refund_transactions = db.scalars(
        select(PaymentTransaction).where(
            PaymentTransaction.order_id == order_id,
            PaymentTransaction.provider == "razorpay",
            PaymentTransaction.provider_refund_id.is_not(None),
        )
    ).all()
    return sum(refund_totals_by_refund_id(refund_transactions).values())


def serialize_transaction(transaction: PaymentTransaction) -> dict:
    return {
        "id": transaction.id,
        "order_id": transaction.order_id,
        "provider": transaction.provider,
        "provider_order_id": transaction.provider_order_id,
        "provider_payment_id": transaction.provider_payment_id,
        "provider_refund_id": transaction.provider_refund_id,
        "event_type": transaction.event_type,
        "status": transaction.status,
        "amount": paise_to_rupees(transaction.amount_paise),
        "currency": transaction.currency,
        "verified": transaction.verified,
        "created_at": transaction.created_at,
    }


@router.get("/transactions", response_model=list[PaymentTransactionOut])
def list_payment_transactions(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    transactions = db.scalars(
        select(PaymentTransaction)
        .order_by(PaymentTransaction.created_at.desc(), PaymentTransaction.id.desc())
        .limit(100)
    ).all()
    return [serialize_transaction(transaction) for transaction in transactions]


@router.post("/razorpay/orders", response_model=RazorpayOrderOut)
def create_razorpay_order(
    payload: RazorpayOrderCreate,
    _current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    require_razorpay_settings(settings)

    request_body = {
        "amount": rupees_to_paise(payload.amount),
        "currency": payload.currency,
        "notes": payload.notes or {},
    }
    if payload.receipt:
        request_body["receipt"] = payload.receipt
    request = Request(
        "https://api.razorpay.com/v1/orders",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": razorpay_auth_header(settings),
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Razorpay rejected the order request ({error.code})",
        ) from error
    except (URLError, TimeoutError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Razorpay. Please retry payment.",
        ) from error

    return {
        "provider": "razorpay",
        "order_id": data["id"],
        "amount": paise_to_rupees(data["amount"]),
        "currency": data["currency"],
        "key_id": settings.razorpay_key_id,
    }


@router.post("/razorpay/verify", response_model=RazorpayVerifyOut)
def verify_razorpay_payment(
    payload: RazorpayVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    require_razorpay_settings(settings)

    verified = verify_razorpay_payment_signature(
        secret=settings.razorpay_key_secret,
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
    )
    record_payment_transaction(
        db,
        event_type="checkout_verified" if verified else "checkout_rejected",
        status_value="verified" if verified else "signature_failed",
        verified=verified,
        provider_order_id=payload.razorpay_order_id,
        provider_payment_id=payload.razorpay_payment_id,
        user=current_user,
        signature=payload.razorpay_signature,
        raw_payload=payload.model_dump(),
    )
    db.commit()

    return {
        "provider": "razorpay",
        "verified": verified,
    }


@router.post("/razorpay/refunds", response_model=RazorpayRefundOut)
def create_razorpay_refund(
    payload: RazorpayRefundCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    require_razorpay_settings(settings)

    order = db.get(Order, payload.order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.payment_method != "razorpay":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only Razorpay orders can be refunded through this endpoint",
        )
    if order.payment_status not in {PaymentStatus.PAID, PaymentStatus.REFUNDED}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only paid Razorpay orders can be refunded",
        )

    payment_transaction = latest_razorpay_payment_transaction(order.id, db)
    if payment_transaction is None or not payment_transaction.provider_payment_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Razorpay payment id is not available for this order",
        )

    already_refunded_paise = refunded_amount_paise(order.id, db)
    refundable_paise = order.total_paise - already_refunded_paise
    if refundable_paise <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This order has already been fully refunded",
        )

    amount_paise = (
        rupees_to_paise(payload.amount)
        if payload.amount is not None
        else refundable_paise
    )
    if amount_paise <= 0 or amount_paise > refundable_paise:
        raise HTTPException(
            status_code=400,
            detail="Refund amount must be between 1 and the remaining refundable amount",
        )

    request_body = {
        "amount": amount_paise,
        "speed": payload.speed,
        "notes": {
            "order_id": str(order.id),
            "order_number": order.order_number,
            "reason": payload.reason or "Admin refund",
        },
    }
    payment_id = payment_transaction.provider_payment_id
    request = Request(
        f"https://api.razorpay.com/v1/payments/{quote(payment_id)}/refund",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": razorpay_auth_header(settings),
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Razorpay rejected the refund request ({error.code})",
        ) from error
    except (URLError, TimeoutError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Razorpay for refund. Please retry.",
        ) from error

    refund_id = data.get("id")
    if not refund_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Razorpay refund response did not include a refund id",
        )

    order.payment_status = (
        PaymentStatus.REFUNDED
        if already_refunded_paise + int(data.get("amount") or amount_paise) >= order.total_paise
        else PaymentStatus.PAID
    )
    record_payment_transaction(
        db,
        event_type="refund_requested",
        status_value=data.get("status", "processed"),
        verified=True,
        provider_order_id=payment_transaction.provider_order_id,
        provider_payment_id=payment_id,
        provider_refund_id=refund_id,
        order=order,
        amount_paise=int(data.get("amount") or amount_paise),
        currency=data.get("currency") or "INR",
        raw_payload=data,
    )
    notify_order_customer(
        db,
        order,
        title="Refund initiated",
        message=f"Refund for order {order.order_number} has been initiated.",
        event_type="payment.refund_requested",
        metadata={"provider": "razorpay", "refund_id": refund_id},
    )
    db.commit()

    return {
        "provider": "razorpay",
        "order_id": order.id,
        "payment_id": payment_id,
        "refund_id": refund_id,
        "amount": paise_to_rupees(int(data.get("amount") or amount_paise)),
        "currency": data.get("currency") or "INR",
        "status": data.get("status", "processed"),
        "payment_status": enum_value(order.payment_status),
    }


@router.get("/razorpay/refunds/{refund_id}", response_model=RazorpayRefundStatusOut)
def read_razorpay_refund_status(
    refund_id: str,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    require_razorpay_settings(settings)

    transaction = db.scalar(
        select(PaymentTransaction)
        .where(
            PaymentTransaction.provider == "razorpay",
            PaymentTransaction.provider_refund_id == refund_id,
        )
        .order_by(PaymentTransaction.created_at.desc(), PaymentTransaction.id.desc())
    )
    if transaction is None:
        raise HTTPException(status_code=404, detail="Refund transaction not found")

    request = Request(
        f"https://api.razorpay.com/v1/refunds/{quote(refund_id)}",
        headers={"Authorization": razorpay_auth_header(settings)},
        method="GET",
    )
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Razorpay rejected the refund status request ({error.code})",
        ) from error
    except (URLError, TimeoutError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Razorpay for refund status. Please retry.",
        ) from error

    transaction.status = data.get("status", transaction.status)
    transaction.amount_paise = int(data.get("amount") or transaction.amount_paise)
    transaction.currency = data.get("currency") or transaction.currency
    transaction.raw_payload = data

    order = transaction.order
    payment_status = None
    if order is not None:
        order.payment_status = (
            PaymentStatus.REFUNDED
            if refunded_amount_paise(order.id, db) >= order.total_paise
            else PaymentStatus.PAID
        )
        payment_status = enum_value(order.payment_status)

    db.commit()
    return {
        "provider": "razorpay",
        "order_id": transaction.order_id,
        "refund_id": refund_id,
        "payment_id": data.get("payment_id") or transaction.provider_payment_id,
        "amount": paise_to_rupees(transaction.amount_paise),
        "currency": transaction.currency,
        "status": transaction.status,
        "payment_status": payment_status,
    }


@router.post("/razorpay/webhook", response_model=RazorpayWebhookOut)
async def receive_razorpay_webhook(
    request: FastAPIRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    if not settings.razorpay_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Razorpay webhook secret is not configured",
        )

    signature = request.headers.get("X-Razorpay-Signature", "")
    body = await request.body()
    verified = verify_razorpay_webhook_signature(
        secret=settings.razorpay_webhook_secret,
        body=body,
        signature=signature,
    )
    if not verified:
        raise HTTPException(status_code=400, detail="Invalid Razorpay webhook signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="Invalid Razorpay webhook body") from error

    event_type = payload.get("event", "unknown")
    event_payload = payload.get("payload") or {}
    payment = (event_payload.get("payment") or {}).get("entity") or {}
    refund = (event_payload.get("refund") or {}).get("entity") or {}
    provider_payment_id = payment.get("id") or refund.get("payment_id")
    provider_order_id = payment.get("order_id")
    provider_refund_id = refund.get("id")
    amount_paise = int(payment.get("amount") or refund.get("amount") or 0)
    currency = payment.get("currency") or refund.get("currency") or "INR"
    status_value = payment.get("status") or refund.get("status") or event_type

    order = find_order_for_payment_event(
        db,
        provider_order_id=provider_order_id,
        provider_payment_id=provider_payment_id,
    )
    payment_status = apply_webhook_payment_status(order, event_type)
    record_payment_transaction(
        db,
        event_type=event_type,
        status_value=status_value,
        verified=True,
        provider_order_id=provider_order_id,
        provider_payment_id=provider_payment_id,
        provider_refund_id=provider_refund_id,
        order=order,
        amount_paise=amount_paise,
        currency=currency,
        signature=signature,
        raw_payload=payload,
    )
    if order is not None:
        if event_type.startswith("refund."):
            order.payment_status = (
                PaymentStatus.REFUNDED
                if refunded_amount_paise(order.id, db) >= order.total_paise
                else PaymentStatus.PAID
            )
            payment_status = enum_value(order.payment_status)
        notify_order_customer(
            db,
            order,
            title="Payment update",
            message=f"Payment status updated to {enum_value(order.payment_status)}.",
            event_type=event_type,
            metadata={"provider": "razorpay"},
        )
    db.commit()

    return {
        "provider": "razorpay",
        "received": True,
        "verified": True,
        "event_type": event_type,
        "payment_status": payment_status,
    }

import base64
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException, Request as FastAPIRequest, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import Settings, get_settings
from app.database import get_db
from app.models import Order, PaymentStatus, PaymentTransaction, User
from app.notifications import notify_order_customer
from app.payment_utils import (
    verify_razorpay_payment_signature,
    verify_razorpay_webhook_signature,
)
from app.schemas import (
    RazorpayOrderCreate,
    RazorpayOrderOut,
    RazorpayWebhookOut,
    RazorpayVerifyOut,
    RazorpayVerifyRequest,
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

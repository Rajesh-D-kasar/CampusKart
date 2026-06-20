import base64
import hashlib
import hmac
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.config import Settings, get_settings
from app.models import User
from app.schemas import (
    RazorpayOrderCreate,
    RazorpayOrderOut,
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


def razorpay_auth_header(settings: Settings) -> str:
    credentials = f"{settings.razorpay_key_id}:{settings.razorpay_key_secret}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
    return f"Basic {encoded}"


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
    _current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    require_razorpay_settings(settings)

    message = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected_signature = hmac.new(
        settings.razorpay_key_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return {
        "provider": "razorpay",
        "verified": hmac.compare_digest(
            expected_signature,
            payload.razorpay_signature,
        ),
    }

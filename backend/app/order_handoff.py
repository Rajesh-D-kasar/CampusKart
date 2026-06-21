from datetime import UTC, datetime
import hashlib
import hmac

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Order, OrderHandoffVerification, OrderStatus

PICKUP_PURPOSE = "pickup"
DROPOFF_PURPOSE = "dropoff"

OTP_READY_STATUSES = {
    OrderStatus.CONFIRMED.value,
    OrderStatus.PACKING.value,
}

DROPOFF_READY_STATUSES = {
    OrderStatus.CONFIRMED.value,
    OrderStatus.PACKING.value,
    OrderStatus.OUT_FOR_DELIVERY.value,
}


def enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def now_utc() -> datetime:
    return datetime.now(UTC)


def handoff_code(order: Order, purpose: str, settings: Settings) -> str:
    message = f"{purpose}:{order.id}:{order.order_number}".encode("utf-8")
    digest = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return f"{int(digest[:12], 16) % 1_000_000:06d}"


def get_handoff(
    order: Order,
    db: Session,
    create: bool = False,
) -> OrderHandoffVerification | None:
    if order.handoff_verification is not None:
        return order.handoff_verification

    handoff = db.scalar(
        select(OrderHandoffVerification).where(
            OrderHandoffVerification.order_id == order.id
        )
    )
    if handoff is None and create:
        handoff = OrderHandoffVerification(order_id=order.id)
        db.add(handoff)
        db.flush()
        order.handoff_verification = handoff
    return handoff


def handoff_state(order: Order, db: Session) -> dict:
    handoff = get_handoff(order, db)
    return {
        "store_ready": bool(handoff and handoff.store_ready_at),
        "store_ready_at": handoff.store_ready_at if handoff else None,
        "pickup_verified": bool(handoff and handoff.pickup_verified_at),
        "dropoff_verified": bool(handoff and handoff.dropoff_verified_at),
        "pickup_verified_at": handoff.pickup_verified_at if handoff else None,
        "dropoff_verified_at": handoff.dropoff_verified_at if handoff else None,
    }


def mark_store_ready(order: Order, db: Session) -> OrderHandoffVerification:
    handoff = get_handoff(order, db, create=True)
    assert handoff is not None
    if handoff.store_ready_at is None:
        handoff.store_ready_at = now_utc()
    return handoff


def shop_pickup_otp(order: Order, db: Session, settings: Settings) -> str | None:
    state = handoff_state(order, db)
    if not state["store_ready"]:
        return None
    if state["pickup_verified"]:
        return None
    if enum_value(order.status) not in OTP_READY_STATUSES:
        return None
    return handoff_code(order, PICKUP_PURPOSE, settings)


def customer_dropoff_otp(order: Order, db: Session, settings: Settings) -> str | None:
    state = handoff_state(order, db)
    if state["dropoff_verified"]:
        return None
    if enum_value(order.status) not in DROPOFF_READY_STATUSES:
        return None
    return handoff_code(order, DROPOFF_PURPOSE, settings)


def verify_handoff_otp(
    order: Order,
    db: Session,
    settings: Settings,
    purpose: str,
    otp: str | None,
) -> OrderHandoffVerification:
    if not otp:
        label = "Pickup" if purpose == PICKUP_PURPOSE else "Customer delivery"
        raise HTTPException(status_code=400, detail=f"{label} OTP is required")

    handoff = get_handoff(order, db, create=True)
    assert handoff is not None

    if purpose == DROPOFF_PURPOSE and handoff.pickup_verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pickup OTP must be verified before customer delivery",
        )
    if purpose == PICKUP_PURPOSE and handoff.store_ready_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Store must mark the order ready before pickup",
        )

    attempts_field = (
        "pickup_attempts" if purpose == PICKUP_PURPOSE else "dropoff_attempts"
    )
    verified_field = (
        "pickup_verified_at" if purpose == PICKUP_PURPOSE else "dropoff_verified_at"
    )

    if getattr(handoff, verified_field) is not None:
        return handoff

    attempts = getattr(handoff, attempts_field) or 0
    max_attempts = handoff.max_attempts or 5
    if attempts >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect OTP attempts. Contact support.",
        )

    expected_otp = handoff_code(order, purpose, settings)
    if not hmac.compare_digest(expected_otp, otp.strip()):
        setattr(handoff, attempts_field, attempts + 1)
        db.commit()
        raise HTTPException(status_code=400, detail="Incorrect OTP")

    setattr(handoff, verified_field, now_utc())
    return handoff

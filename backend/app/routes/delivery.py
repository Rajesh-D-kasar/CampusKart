from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_delivery_partner
from app.config import Settings, get_settings
from app.database import get_db
from app.models import DeliveryLocation, Order, OrderStatus, PaymentStatus, User, UserRole
from app.notifications import notify_order_customer
from app.order_handoff import (
    DROPOFF_PURPOSE,
    PICKUP_PURPOSE,
    handoff_state,
    lifecycle_events,
    verify_handoff_otp,
)
from app.order_ops import (
    finalize_reserved_inventory,
    latest_delivery_location,
    serialize_delivery_location,
    serialize_order_item,
)
from app.schemas import (
    DeliveryLocationOut,
    DeliveryLocationUpdate,
    DeliveryOrderOut,
    DeliveryOrderStatusUpdate,
    DeliverySummaryOut,
)
from app.tracking import assigned_partner_email, tracking_detail

router = APIRouter(prefix="/delivery", tags=["delivery"])

VISIBLE_STATUSES = {
    OrderStatus.CONFIRMED,
    OrderStatus.PACKING,
    OrderStatus.OUT_FOR_DELIVERY,
    OrderStatus.DELIVERED,
}

ALLOWED_TRANSITIONS = {
    OrderStatus.CONFIRMED: {OrderStatus.OUT_FOR_DELIVERY},
    OrderStatus.PACKING: {OrderStatus.OUT_FOR_DELIVERY},
    OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: {OrderStatus.DELIVERED},
}


def paise_to_rupees(value: int) -> float:
    return value / 100


def enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def order_options():
    return (
        selectinload(Order.items),
        selectinload(Order.user),
        selectinload(Order.assigned_delivery_partner),
        selectinload(Order.delivery_locations),
    )


def can_access_order(order: Order, current_user: User) -> bool:
    if current_user.role == UserRole.ADMIN:
        return enum_value(order.status) != OrderStatus.CANCELLED.value
    return assigned_partner_email(order) == current_user.email


def serialize_delivery_order(order: Order, db: Session) -> dict:
    item_count = sum(item.quantity for item in order.items)
    snapshot = order.delivery_address_snapshot or {}
    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": enum_value(order.status),
        "payment_status": enum_value(order.payment_status),
        "payment_method": order.payment_method,
        "item_count": item_count,
        "subtotal": paise_to_rupees(order.subtotal_paise),
        "delivery_fee": paise_to_rupees(order.delivery_fee_paise),
        "discount": paise_to_rupees(order.discount_paise),
        "total": paise_to_rupees(order.total_paise),
        **tracking_detail(order),
        "delivery_location": serialize_delivery_location(latest_delivery_location(order)),
        "created_at": order.created_at,
        "address_id": order.address_id,
        "delivery_address_snapshot": snapshot,
        "delivery_instruction": order.delivery_instruction,
        "customer_delivery_otp": None,
        **handoff_state(order, db),
        "lifecycle_events": lifecycle_events(order, db),
        "items": [serialize_order_item(item) for item in order.items],
        "updated_at": order.updated_at,
        "customer_name": order.user.full_name,
        "customer_email": order.user.email,
        "customer_phone": order.user.phone,
        "delivery_city": snapshot.get("city"),
    }


def get_accessible_order(order_id: int, current_user: User, db: Session) -> Order:
    order = db.scalar(
        select(Order).options(*order_options()).where(Order.id == order_id)
    )
    if order is None or not can_access_order(order, current_user):
        raise HTTPException(status_code=404, detail="Delivery order not found")
    return order


def list_accessible_delivery_orders(current_user: User, db: Session) -> list[Order]:
    orders = db.scalars(
        select(Order)
        .options(*order_options())
        .where(Order.status.in_(VISIBLE_STATUSES))
        .order_by(Order.created_at.desc(), Order.id.desc())
    ).all()
    return [order for order in orders if can_access_order(order, current_user)]


def serialize_delivery_summary(orders: list[Order]) -> dict:
    return {
        "active_orders": sum(
            1 for order in orders if order.status != OrderStatus.DELIVERED
        ),
        "packing_orders": sum(
            1
            for order in orders
            if order.status in {OrderStatus.CONFIRMED, OrderStatus.PACKING}
        ),
        "out_for_delivery_orders": sum(
            1 for order in orders if order.status == OrderStatus.OUT_FOR_DELIVERY
        ),
        "delivered_orders": sum(
            1 for order in orders if order.status == OrderStatus.DELIVERED
        ),
        "cod_collection_due": paise_to_rupees(
            sum(
                order.total_paise
                for order in orders
                if order.payment_method == "cash_on_delivery"
                and order.payment_status == PaymentStatus.PENDING
                and order.status != OrderStatus.DELIVERED
            )
        ),
        "delivered_value": paise_to_rupees(
            sum(
                order.total_paise
                for order in orders
                if order.status == OrderStatus.DELIVERED
            )
        ),
    }


@router.get("/summary", response_model=DeliverySummaryOut)
def read_delivery_summary(
    current_user: User = Depends(require_delivery_partner),
    db: Session = Depends(get_db),
) -> dict:
    return serialize_delivery_summary(list_accessible_delivery_orders(current_user, db))


@router.get("/orders", response_model=list[DeliveryOrderOut])
def list_delivery_orders(
    current_user: User = Depends(require_delivery_partner),
    db: Session = Depends(get_db),
) -> list[dict]:
    return [
        serialize_delivery_order(order, db)
        for order in list_accessible_delivery_orders(current_user, db)
    ]


@router.post("/orders/{order_id}/location", response_model=DeliveryLocationOut)
def update_delivery_location(
    order_id: int,
    payload: DeliveryLocationUpdate,
    current_user: User = Depends(require_delivery_partner),
    db: Session = Depends(get_db),
) -> dict:
    order = get_accessible_order(order_id, current_user, db)
    if order.status not in {OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Location can be shared after pickup starts",
        )

    location = DeliveryLocation(
        order_id=order.id,
        delivery_partner_id=current_user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_meters=payload.accuracy_meters,
        battery_percent=payload.battery_percent,
        source=payload.source,
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return serialize_delivery_location(location)


@router.patch("/orders/{order_id}/status", response_model=DeliveryOrderOut)
def update_delivery_order_status(
    order_id: int,
    payload: DeliveryOrderStatusUpdate,
    current_user: User = Depends(require_delivery_partner),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    order = get_accessible_order(order_id, current_user, db)
    next_status = OrderStatus(payload.status)

    if next_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This delivery status transition is not allowed",
        )

    if next_status == OrderStatus.OUT_FOR_DELIVERY:
        verify_handoff_otp(order, db, settings, PICKUP_PURPOSE, payload.otp)
    if next_status == OrderStatus.DELIVERED:
        verify_handoff_otp(order, db, settings, DROPOFF_PURPOSE, payload.otp)

    previous_status = order.status
    order.status = next_status
    if order.status == OrderStatus.DELIVERED and previous_status != OrderStatus.DELIVERED:
        finalize_reserved_inventory(order, db)
    if order.status == OrderStatus.DELIVERED and order.payment_method == "cash_on_delivery":
        order.payment_status = PaymentStatus.PAID
    if previous_status != order.status:
        notify_order_customer(
            db,
            order,
            title="Delivery update",
            message=f"Order {order.order_number} is now {enum_value(order.status)}.",
            event_type=f"delivery.{enum_value(order.status)}",
        )

    db.commit()
    saved_order = get_accessible_order(order_id, current_user, db)
    return serialize_delivery_order(saved_order, db)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_delivery_partner
from app.database import get_db
from app.models import Order, OrderStatus, PaymentStatus, User, UserRole
from app.schemas import DeliveryOrderOut, DeliveryOrderStatusUpdate
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
    return selectinload(Order.items), selectinload(Order.user)


def can_access_order(order: Order, current_user: User) -> bool:
    if current_user.role == UserRole.ADMIN:
        return enum_value(order.status) != OrderStatus.CANCELLED.value
    return assigned_partner_email(order) == current_user.email


def serialize_delivery_order(order: Order) -> dict:
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
        "created_at": order.created_at,
        "address_id": order.address_id,
        "delivery_address_snapshot": snapshot,
        "delivery_instruction": order.delivery_instruction,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "unit": item.unit,
                "unit_price": paise_to_rupees(item.unit_price_paise),
                "quantity": item.quantity,
                "line_total": paise_to_rupees(item.line_total_paise),
            }
            for item in order.items
        ],
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


@router.get("/orders", response_model=list[DeliveryOrderOut])
def list_delivery_orders(
    current_user: User = Depends(require_delivery_partner),
    db: Session = Depends(get_db),
) -> list[dict]:
    orders = db.scalars(
        select(Order)
        .options(*order_options())
        .where(Order.status.in_(VISIBLE_STATUSES))
        .order_by(Order.created_at.desc(), Order.id.desc())
    ).all()
    return [
        serialize_delivery_order(order)
        for order in orders
        if can_access_order(order, current_user)
    ]


@router.patch("/orders/{order_id}/status", response_model=DeliveryOrderOut)
def update_delivery_order_status(
    order_id: int,
    payload: DeliveryOrderStatusUpdate,
    current_user: User = Depends(require_delivery_partner),
    db: Session = Depends(get_db),
) -> dict:
    order = get_accessible_order(order_id, current_user, db)
    next_status = OrderStatus(payload.status)

    if next_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This delivery status transition is not allowed",
        )

    order.status = next_status
    if order.status == OrderStatus.DELIVERED and order.payment_method == "cash_on_delivery":
        order.payment_status = PaymentStatus.PAID

    db.commit()
    saved_order = get_accessible_order(order_id, current_user, db)
    return serialize_delivery_order(saved_order)

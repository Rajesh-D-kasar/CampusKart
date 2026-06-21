from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.config import Settings, get_settings
from app.database import get_db
from app.models import (
    Address,
    CartItem,
    Inventory,
    Order,
    OrderItem,
    PaymentStatus,
    Product,
    Store,
    User,
)
from app.order_handoff import customer_dropoff_otp, handoff_state
from app.promotions import PromotionError, apply_coupon
from app.routes.cart import (
    DELIVERY_FEE_PAISE,
    FREE_DELIVERY_THRESHOLD_PAISE,
    get_or_create_cart,
)
from app.schemas import OrderCreate, OrderOut, OrderSummaryOut
from app.tracking import tracking_detail, tracking_summary

router = APIRouter(prefix="/orders", tags=["orders"])


def paise_to_rupees(value: int) -> float:
    return value / 100


def enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def generate_order_number(user_id: int) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%y%m%d%H%M%S")
    return f"CK{timestamp}{user_id}{uuid4().hex[:6].upper()}"


def address_snapshot(address: Address) -> dict[str, str | None]:
    return {
        "label": address.label,
        "receiver_name": address.receiver_name,
        "phone": address.phone,
        "line1": address.line1,
        "line2": address.line2,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
    }


def serialize_order_summary(order: Order) -> dict:
    item_count = sum(item.quantity for item in order.items)
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
        **tracking_summary(order),
        "created_at": order.created_at,
    }


def serialize_order(order: Order, db: Session, settings: Settings) -> dict:
    data = serialize_order_summary(order)
    data.update(
        {
            "address_id": order.address_id,
            "delivery_address_snapshot": order.delivery_address_snapshot,
            "delivery_instruction": order.delivery_instruction,
            **tracking_detail(order),
            "customer_delivery_otp": customer_dropoff_otp(order, db, settings),
            **handoff_state(order, db),
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
        }
    )
    return data


def order_options():
    return selectinload(Order.items), selectinload(Order.assigned_delivery_partner)


def get_owned_order(order_id: int, user_id: int, db: Session) -> Order:
    order = db.scalar(
        select(Order)
        .options(*order_options())
        .where(Order.id == order_id, Order.user_id == user_id)
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def get_owned_address(address_id: int, user_id: int, db: Session) -> Address:
    address = db.scalar(
        select(Address).where(Address.id == address_id, Address.user_id == user_id)
    )
    if address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


def get_active_store(db: Session) -> Store:
    store = db.scalar(select(Store).where(Store.is_active.is_(True)).order_by(Store.id))
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No active store is available",
        )
    return store


def inventory_for_store(product: Product, store_id: int) -> Inventory | None:
    return next(
        (item for item in product.inventory_items if item.store_id == store_id),
        None,
    )


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def place_order(
    payload: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    cart = get_or_create_cart(current_user, db)
    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    address = get_owned_address(payload.address_id, current_user.id, db)
    store = get_active_store(db)

    if (
        payload.payment_method in {"upi", "card"}
        and payload.mock_payment_result == "failed"
    ):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment failed. Please try again or choose cash on delivery.",
        )

    subtotal_paise = 0
    reserved_items: list[tuple[Inventory, int]] = []
    order_items: list[OrderItem] = []

    for cart_item in cart.items:
        inventory = inventory_for_store(cart_item.product, store.id)
        if inventory is None or inventory.available_quantity < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{cart_item.product.name} does not have enough stock",
            )

        line_total_paise = cart_item.product.price_paise * cart_item.quantity
        subtotal_paise += line_total_paise
        reserved_items.append((inventory, cart_item.quantity))
        order_items.append(
            OrderItem(
                product_id=cart_item.product_id,
                product_name=cart_item.product.name,
                unit=cart_item.product.unit,
                unit_price_paise=cart_item.product.price_paise,
                quantity=cart_item.quantity,
                line_total_paise=line_total_paise,
            )
        )

    delivery_fee_paise = (
        0
        if subtotal_paise >= FREE_DELIVERY_THRESHOLD_PAISE
        else DELIVERY_FEE_PAISE
    )

    try:
        promotion = apply_coupon(
            subtotal_paise=subtotal_paise,
            delivery_fee_paise=delivery_fee_paise,
            code=payload.promo_code,
        )
    except PromotionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    delivery_fee_paise = promotion.delivery_fee_paise
    discount_paise = promotion.discount_paise

    order = Order(
        order_number=generate_order_number(current_user.id),
        user_id=current_user.id,
        store_id=store.id,
        address_id=address.id,
        delivery_address_snapshot=address_snapshot(address),
        payment_method=payload.payment_method,
        payment_status=(
            PaymentStatus.PAID
            if payload.payment_method in {"upi", "card"}
            else PaymentStatus.PENDING
        ),
        subtotal_paise=subtotal_paise,
        delivery_fee_paise=delivery_fee_paise,
        discount_paise=discount_paise,
        total_paise=subtotal_paise + delivery_fee_paise - discount_paise,
        delivery_instruction=payload.delivery_instruction,
    )
    order.items.extend(order_items)
    db.add(order)

    for inventory, quantity in reserved_items:
        inventory.reserved_quantity += quantity

    for cart_item in list(cart.items):
        db.delete(cart_item)

    db.commit()

    saved_order = get_owned_order(order.id, current_user.id, db)
    return serialize_order(saved_order, db, settings)


@router.get("", response_model=list[OrderSummaryOut])
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    orders = db.scalars(
        select(Order)
        .options(*order_options())
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    ).all()
    return [serialize_order_summary(order) for order in orders]


@router.get("/{order_id}", response_model=OrderOut)
def read_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    return serialize_order(get_owned_order(order_id, current_user.id, db), db, settings)

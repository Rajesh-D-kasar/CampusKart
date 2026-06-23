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
    OrderReview,
    OrderStatus,
    PaymentStatus,
    PaymentTransaction,
    Product,
    Store,
    User,
)
from app.notifications import notify_order_customer
from app.order_handoff import customer_dropoff_otp, handoff_state, lifecycle_events
from app.order_ops import (
    cancel_order,
    invoice_for_order,
    latest_delivery_location,
    serialize_delivery_location,
    serialize_order_item,
    serialize_order_review,
)
from app.payment_utils import verify_razorpay_payment_signature
from app.promotions import PromotionError, apply_coupon
from app.routes.cart import (
    DELIVERY_FEE_PAISE,
    FREE_DELIVERY_THRESHOLD_PAISE,
    get_or_create_cart,
)
from app.schemas import (
    OrderCancelRequest,
    OrderCreate,
    OrderInvoiceOut,
    OrderOut,
    OrderReviewCreate,
    OrderReviewOut,
    OrderSummaryOut,
)
from app.tracking import tracking_detail, tracking_summary
from app.wallet import record_wallet_transaction

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
        "delivery_location": serialize_delivery_location(latest_delivery_location(order)),
        "review": serialize_order_review(order.review),
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
            "lifecycle_events": lifecycle_events(order, db),
            "items": [serialize_order_item(item) for item in order.items],
            "updated_at": order.updated_at,
        }
    )
    return data


def order_options():
    return (
        selectinload(Order.items),
        selectinload(Order.user),
        selectinload(Order.assigned_delivery_partner),
        selectinload(Order.delivery_locations),
        selectinload(Order.review),
    )


def get_owned_order(order_id: int, user_id: int, db: Session) -> Order:
    order = db.scalar(
        select(Order)
        .options(*order_options())
        .where(Order.id == order_id, Order.user_id == user_id)
        .execution_options(populate_existing=True)
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
    if payload.payment_method == "razorpay":
        if not settings.razorpay_key_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Razorpay credentials are not configured",
            )
        if not (
            payload.razorpay_order_id
            and payload.razorpay_payment_id
            and payload.razorpay_signature
        ):
            raise HTTPException(
                status_code=400,
                detail="Razorpay payment proof is required",
            )
        if not verify_razorpay_payment_signature(
            secret=settings.razorpay_key_secret,
            razorpay_order_id=payload.razorpay_order_id,
            razorpay_payment_id=payload.razorpay_payment_id,
            razorpay_signature=payload.razorpay_signature,
        ):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Razorpay payment verification failed",
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
            if payload.payment_method in {"upi", "card", "razorpay"}
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
    db.flush()

    if payload.payment_method == "razorpay":
        db.add(
            PaymentTransaction(
                order_id=order.id,
                user_id=current_user.id,
                provider="razorpay",
                provider_order_id=payload.razorpay_order_id,
                provider_payment_id=payload.razorpay_payment_id,
                event_type="order_paid",
                status="paid",
                amount_paise=order.total_paise,
                currency="INR",
                verified=True,
                signature=payload.razorpay_signature,
                raw_payload={
                    "source": "checkout",
                    "order_number": order.order_number,
                },
            )
        )
    notify_order_customer(
        db,
        order,
        title="Order placed",
        message=f"Order {order.order_number} placed successfully.",
        event_type="order.placed",
    )

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
        .execution_options(populate_existing=True)
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


def normalized_issue_tags(tags: list[str]) -> list[str]:
    cleaned = []
    for tag in tags:
        value = tag.strip().lower().replace(" ", "_")
        if not value:
            continue
        if len(value) > 40:
            raise HTTPException(status_code=400, detail="Issue tag is too long")
        if value not in cleaned:
            cleaned.append(value)
    if len(cleaned) > 6:
        raise HTTPException(status_code=400, detail="Select up to 6 issue tags")
    return cleaned


@router.put("/{order_id}/review", response_model=OrderReviewOut)
def submit_order_review(
    order_id: int,
    payload: OrderReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    order = get_owned_order(order_id, current_user.id, db)
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review can be submitted only after delivery",
        )

    comment = payload.comment.strip() if payload.comment else None
    review = db.scalar(select(OrderReview).where(OrderReview.order_id == order.id))
    if review is None:
        review = OrderReview(
            order_id=order.id,
            user_id=current_user.id,
            store_id=order.store_id,
            delivery_partner_id=order.assigned_delivery_partner_id,
            overall_rating=payload.overall_rating,
            product_rating=payload.product_rating,
            delivery_rating=payload.delivery_rating,
            seller_rating=payload.seller_rating,
            comment=comment,
            issue_tags=normalized_issue_tags(payload.issue_tags),
        )
        db.add(review)
    else:
        review.overall_rating = payload.overall_rating
        review.product_rating = payload.product_rating
        review.delivery_rating = payload.delivery_rating
        review.seller_rating = payload.seller_rating
        review.comment = comment
        review.issue_tags = normalized_issue_tags(payload.issue_tags)
        review.delivery_partner_id = order.assigned_delivery_partner_id
        review.store_id = order.store_id

    db.commit()
    db.refresh(review)
    return serialize_order_review(review)


@router.patch("/{order_id}/cancel", response_model=OrderOut)
def cancel_my_order(
    order_id: int,
    payload: OrderCancelRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    order = get_owned_order(order_id, current_user.id, db)
    previous_payment_status = order.payment_status
    try:
        cancel_order(order, db)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    if previous_payment_status == PaymentStatus.PAID:
        db.add(
            PaymentTransaction(
                order_id=order.id,
                user_id=current_user.id,
                provider=order.payment_method,
                event_type="refund_initiated",
                status="refunded",
                amount_paise=order.total_paise,
                currency="INR",
                verified=True,
                raw_payload={"reason": payload.reason if payload else None},
            )
        )
        record_wallet_transaction(
            db,
            user=current_user,
            order=order,
            amount_paise=order.total_paise,
            transaction_type="refund_credit",
            description=f"Refund credit for cancelled order {order.order_number}",
            reference=f"cancel-refund-{order.id}",
            metadata={"reason": payload.reason if payload else None},
        )
    notify_order_customer(
        db,
        order,
        title="Order cancelled",
        message=f"Order {order.order_number} has been cancelled.",
        event_type="order.cancelled",
        metadata={"reason": payload.reason if payload else None},
    )
    db.commit()
    saved_order = get_owned_order(order_id, current_user.id, db)
    return serialize_order(saved_order, db, settings)


@router.get("/{order_id}/invoice", response_model=OrderInvoiceOut)
def read_order_invoice(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    order = get_owned_order(order_id, current_user.id, db)
    return invoice_for_order(order)

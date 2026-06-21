from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    DeliveryLocation,
    Inventory,
    Order,
    OrderItem,
    OrderStatus,
    PaymentStatus,
    PaymentTransaction,
)


def enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def inventory_for_order_item(
    db: Session,
    item: OrderItem,
    store_id: int,
) -> Inventory | None:
    if item.product_id is None:
        return None
    return db.scalar(
        select(Inventory).where(
            Inventory.product_id == item.product_id,
            Inventory.store_id == store_id,
        )
    )


def release_reserved_inventory(order: Order, db: Session) -> None:
    for item in order.items:
        inventory = inventory_for_order_item(db, item, order.store_id)
        if inventory is None:
            continue
        inventory.reserved_quantity = max(0, inventory.reserved_quantity - item.quantity)


def finalize_reserved_inventory(order: Order, db: Session) -> None:
    for item in order.items:
        inventory = inventory_for_order_item(db, item, order.store_id)
        if inventory is None:
            continue
        inventory.reserved_quantity = max(0, inventory.reserved_quantity - item.quantity)
        inventory.stock_quantity = max(0, inventory.stock_quantity - item.quantity)


def cancel_order(order: Order, db: Session) -> None:
    if order.status == OrderStatus.CANCELLED:
        return
    if order.status in {OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED}:
        raise ValueError("Cannot cancel an order after pickup has started")

    release_reserved_inventory(order, db)
    order.status = OrderStatus.CANCELLED
    if order.payment_status == PaymentStatus.PAID:
        order.payment_status = PaymentStatus.REFUNDED


def serialize_order_item(item: OrderItem) -> dict:
    return {
        "id": item.id,
        "product_id": item.product_id,
        "product_name": item.product_name,
        "unit": item.unit,
        "unit_price": item.unit_price_paise / 100,
        "quantity": item.quantity,
        "line_total": item.line_total_paise / 100,
        "packed_quantity": item.packed_quantity,
        "fulfillment_status": item.fulfillment_status,
        "substitution_note": item.substitution_note,
    }


def latest_delivery_location(order: Order) -> DeliveryLocation | None:
    if not order.delivery_locations:
        return None
    return max(order.delivery_locations, key=lambda location: location.created_at)


def serialize_delivery_location(location: DeliveryLocation | None) -> dict | None:
    if location is None:
        return None
    return {
        "id": location.id,
        "latitude": float(location.latitude),
        "longitude": float(location.longitude),
        "accuracy_meters": (
            float(location.accuracy_meters)
            if location.accuracy_meters is not None
            else None
        ),
        "battery_percent": location.battery_percent,
        "source": location.source,
        "created_at": location.created_at,
    }


def refund_totals_by_refund_id(transactions: list[PaymentTransaction]) -> dict[str, int]:
    latest_amounts: dict[str, tuple[int, int]] = {}
    for transaction in transactions:
        if not transaction.provider_refund_id:
            continue
        transaction_id = transaction.id or 0
        current = latest_amounts.get(transaction.provider_refund_id)
        if current is None or transaction_id >= current[0]:
            latest_amounts[transaction.provider_refund_id] = (
                transaction_id,
                transaction.amount_paise,
            )
    return {
        refund_id: amount
        for refund_id, (_transaction_id, amount) in latest_amounts.items()
    }


def serialize_payment_transaction(transaction: PaymentTransaction) -> dict:
    return {
        "id": transaction.id,
        "order_id": transaction.order_id,
        "provider": transaction.provider,
        "provider_order_id": transaction.provider_order_id,
        "provider_payment_id": transaction.provider_payment_id,
        "provider_refund_id": transaction.provider_refund_id,
        "event_type": transaction.event_type,
        "status": transaction.status,
        "amount": transaction.amount_paise / 100,
        "currency": transaction.currency,
        "verified": transaction.verified,
        "created_at": transaction.created_at,
    }


def invoice_for_order(order: Order) -> dict:
    return {
        "invoice_number": f"INV-{order.order_number}",
        "order_id": order.id,
        "order_number": order.order_number,
        "status": enum_value(order.status),
        "payment_status": enum_value(order.payment_status),
        "payment_method": order.payment_method,
        "customer_name": order.user.full_name,
        "customer_email": order.user.email,
        "delivery_address_snapshot": order.delivery_address_snapshot,
        "items": [serialize_order_item(item) for item in order.items],
        "subtotal": order.subtotal_paise / 100,
        "delivery_fee": order.delivery_fee_paise / 100,
        "discount": order.discount_paise / 100,
        "total": order.total_paise / 100,
        "created_at": order.created_at,
    }

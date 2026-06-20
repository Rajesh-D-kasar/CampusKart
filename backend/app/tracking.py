from datetime import datetime, timedelta

from app.models import Order, OrderStatus

TRACKING_FLOW = [
    {
        "key": OrderStatus.PLACED.value,
        "label": "Order placed",
        "description": "We received your order and shared it with the store.",
        "offset_minutes": 0,
    },
    {
        "key": OrderStatus.CONFIRMED.value,
        "label": "Store confirmed",
        "description": "The store has accepted the order and started fulfillment.",
        "offset_minutes": 2,
    },
    {
        "key": OrderStatus.PACKING.value,
        "label": "Packing items",
        "description": "Your items are being picked, packed, and quality checked.",
        "offset_minutes": 6,
    },
    {
        "key": OrderStatus.OUT_FOR_DELIVERY.value,
        "label": "Out for delivery",
        "description": "Your delivery partner is on the way.",
        "offset_minutes": 14,
    },
    {
        "key": OrderStatus.DELIVERED.value,
        "label": "Delivered",
        "description": "Your order has reached the delivery address.",
        "offset_minutes": 22,
    },
]

ETA_MINUTES_BY_STATUS = {
    OrderStatus.PLACED.value: 22,
    OrderStatus.CONFIRMED.value: 18,
    OrderStatus.PACKING.value: 12,
    OrderStatus.OUT_FOR_DELIVERY.value: 7,
    OrderStatus.DELIVERED.value: 0,
}

DELIVERY_PARTNERS = [
    {
        "name": "Aman Delivery",
        "email": "delivery1@campuskart.com",
        "phone": "+91 90000 11101",
        "vehicle_number": "MH 12 CK 2041",
    },
    {
        "name": "Rohit Runner",
        "email": "delivery2@campuskart.com",
        "phone": "+91 90000 11102",
        "vehicle_number": "MH 12 CK 3198",
    },
    {
        "name": "Priya Express",
        "email": "delivery3@campuskart.com",
        "phone": "+91 90000 11103",
        "vehicle_number": "MH 12 CK 4427",
    },
]

PARTNER_STATUSES = {
    OrderStatus.CONFIRMED.value,
    OrderStatus.PACKING.value,
    OrderStatus.OUT_FOR_DELIVERY.value,
    OrderStatus.DELIVERED.value,
}


def enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def order_status(order: Order) -> str:
    return enum_value(order.status)


def estimate_delivery_at(order: Order) -> datetime | None:
    status = order_status(order)
    eta_minutes = ETA_MINUTES_BY_STATUS.get(status)

    if eta_minutes is None:
        return None
    if eta_minutes == 0:
        return order.updated_at or order.created_at

    return (order.updated_at or order.created_at) + timedelta(minutes=eta_minutes)


def eta_minutes(order: Order) -> int | None:
    return ETA_MINUTES_BY_STATUS.get(order_status(order))


def delivery_partner(order: Order) -> dict[str, str] | None:
    if order_status(order) not in PARTNER_STATUSES or order.id is None:
        return None
    return DELIVERY_PARTNERS[order.id % len(DELIVERY_PARTNERS)]


def assigned_partner_email(order: Order) -> str | None:
    partner = delivery_partner(order)
    return partner["email"] if partner else None


def tracking_message(order: Order) -> str:
    status = order_status(order)
    partner = delivery_partner(order)

    if status == OrderStatus.PLACED.value:
        return "Order received. Store confirmation should happen shortly."
    if status == OrderStatus.CONFIRMED.value:
        return "Store confirmed your order. Packing will start soon."
    if status == OrderStatus.PACKING.value:
        return "Items are being packed and checked for freshness."
    if status == OrderStatus.OUT_FOR_DELIVERY.value and partner:
        return f"{partner['name']} is on the way to your address."
    if status == OrderStatus.DELIVERED.value:
        return "Delivered successfully. Thanks for shopping with CampusKart."
    if status == OrderStatus.CANCELLED.value:
        return "This order has been cancelled."
    return "Tracking is being updated."


def delivery_progress_percent(order: Order) -> int:
    status = order_status(order)
    if status == OrderStatus.CANCELLED.value:
        return 100

    keys = [step["key"] for step in TRACKING_FLOW]
    try:
        index = keys.index(status)
    except ValueError:
        return 0

    return round((index / (len(TRACKING_FLOW) - 1)) * 100)


def tracking_steps(order: Order) -> list[dict]:
    status = order_status(order)

    if status == OrderStatus.CANCELLED.value:
        return [
            {
                "key": OrderStatus.PLACED.value,
                "label": "Order placed",
                "description": "We received your order.",
                "completed": True,
                "current": False,
                "timestamp": order.created_at,
            },
            {
                "key": OrderStatus.CANCELLED.value,
                "label": "Cancelled",
                "description": "The order was cancelled before delivery.",
                "completed": True,
                "current": True,
                "timestamp": order.updated_at or order.created_at,
            },
        ]

    keys = [step["key"] for step in TRACKING_FLOW]
    try:
        current_index = keys.index(status)
    except ValueError:
        current_index = 0

    steps = []
    for index, step in enumerate(TRACKING_FLOW):
        completed = index <= current_index
        current = index == current_index
        timestamp = None

        if completed:
            timestamp = order.created_at + timedelta(minutes=step["offset_minutes"])
            if current:
                timestamp = order.updated_at or timestamp

        steps.append(
            {
                "key": step["key"],
                "label": step["label"],
                "description": step["description"],
                "completed": completed,
                "current": current,
                "timestamp": timestamp,
            }
        )

    return steps


def tracking_summary(order: Order) -> dict:
    return {
        "eta_minutes": eta_minutes(order),
        "estimated_delivery_at": estimate_delivery_at(order),
        "delivery_partner": delivery_partner(order),
        "tracking_message": tracking_message(order),
    }


def tracking_detail(order: Order) -> dict:
    return {
        **tracking_summary(order),
        "delivery_progress_percent": delivery_progress_percent(order),
        "tracking_steps": tracking_steps(order),
    }

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Order, OrderStatus, User, UserRole

PARTNER_VEHICLES = {
    "delivery1@campuskart.com": "MH 12 CK 2041",
    "delivery2@campuskart.com": "MH 12 CK 3198",
    "delivery3@campuskart.com": "MH 12 CK 4427",
}

ACTIVE_DELIVERY_STATUSES = {
    OrderStatus.CONFIRMED,
    OrderStatus.PACKING,
    OrderStatus.OUT_FOR_DELIVERY,
}


def partner_profile(user: User | None) -> dict[str, str] | None:
    if user is None:
        return None
    phone = user.phone or "Not available"
    if phone.isdigit() and len(phone) == 10:
        phone = f"+91 {phone[:5]} {phone[5:]}"
    return {
        "name": user.full_name,
        "phone": phone,
        "vehicle_number": PARTNER_VEHICLES.get(user.email, "Vehicle updating"),
    }


def delivery_partner(order: Order) -> dict[str, str] | None:
    status = order.status.value if hasattr(order.status, "value") else str(order.status)
    if status not in {item.value for item in ACTIVE_DELIVERY_STATUSES} | {
        OrderStatus.DELIVERED.value
    }:
        return None
    return partner_profile(order.assigned_delivery_partner)


def assigned_partner_email(order: Order) -> str | None:
    return order.assigned_delivery_partner.email if order.assigned_delivery_partner else None


def delivery_partners(db: Session) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .where(
                User.role == UserRole.DELIVERY_PARTNER,
                User.is_active.is_(True),
            )
            .order_by(User.full_name)
        ).all()
    )


def active_order_count(partner_id: int, db: Session) -> int:
    return int(
        db.scalar(
            select(func.count(Order.id)).where(
                Order.assigned_delivery_partner_id == partner_id,
                Order.status.in_(ACTIVE_DELIVERY_STATUSES),
            )
        )
        or 0
    )


def serialize_delivery_partner(user: User, db: Session) -> dict:
    profile = partner_profile(user) or {}
    return {
        "id": user.id,
        "email": user.email,
        "name": profile.get("name", user.full_name),
        "phone": profile.get("phone", user.phone or "Not available"),
        "vehicle_number": profile.get("vehicle_number", "Vehicle updating"),
        "active_order_count": active_order_count(user.id, db),
    }


def choose_delivery_partner(db: Session) -> User | None:
    partners = delivery_partners(db)
    if not partners:
        return None
    return min(partners, key=lambda partner: (active_order_count(partner.id, db), partner.id))


def ensure_delivery_assignment(order: Order, db: Session) -> User | None:
    if order.assigned_delivery_partner is not None:
        return order.assigned_delivery_partner
    partner = choose_delivery_partner(db)
    if partner is None:
        return None
    order.assigned_delivery_partner = partner
    order.assigned_delivery_partner_id = partner.id
    return partner

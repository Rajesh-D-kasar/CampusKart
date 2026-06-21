from sqlalchemy.orm import Session

from app.models import Notification, Order


def create_notification(
    db: Session,
    *,
    user_id: int | None,
    title: str,
    message: str,
    event_type: str,
    order: Order | None = None,
    metadata: dict | None = None,
) -> Notification | None:
    if user_id is None:
        return None

    notification = Notification(
        user_id=user_id,
        order_id=order.id if order else None,
        event_type=event_type,
        title=title,
        message=message,
        metadata_json=metadata or {},
    )
    db.add(notification)
    return notification


def notify_order_customer(
    db: Session,
    order: Order,
    *,
    title: str,
    message: str,
    event_type: str,
    metadata: dict | None = None,
) -> Notification | None:
    return create_notification(
        db,
        user_id=order.user_id,
        title=title,
        message=message,
        event_type=event_type,
        order=order,
        metadata=metadata,
    )

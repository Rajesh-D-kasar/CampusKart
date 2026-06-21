from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models import Order, SupportTicket, User, UserRole
from app.schemas import SupportTicketCreate, SupportTicketOut, SupportTicketUpdate

router = APIRouter(tags=["support"])


def role_audience(user: User) -> str:
    if user.role == UserRole.DELIVERY_PARTNER:
        return "delivery"
    if user.role == UserRole.ADMIN:
        return "seller"
    return "customer"


def enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def ticket_options():
    return selectinload(SupportTicket.requester), selectinload(SupportTicket.order)


def serialize_ticket(ticket: SupportTicket) -> dict:
    return {
        "id": ticket.id,
        "audience": ticket.audience,
        "category": ticket.category,
        "subject": ticket.subject,
        "message": ticket.message,
        "status": ticket.status,
        "priority": ticket.priority,
        "resolution": ticket.resolution,
        "order_id": ticket.order_id,
        "order_number": ticket.order.order_number if ticket.order else None,
        "requester_name": ticket.requester.full_name,
        "requester_email": ticket.requester.email,
        "requester_role": enum_value(ticket.requester.role),
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
    }


def can_reference_order(order: Order, user: User) -> bool:
    if user.role == UserRole.ADMIN:
        return True
    if user.role == UserRole.DELIVERY_PARTNER:
        return order.assigned_delivery_partner_id == user.id
    return order.user_id == user.id


def validate_order_reference(
    order_id: int | None, user: User, db: Session
) -> Order | None:
    if order_id is None:
        return None
    order = db.get(Order, order_id)
    if order is None or not can_reference_order(order, user):
        raise HTTPException(status_code=404, detail="Order not found for support")
    return order


@router.post(
    "/support/tickets",
    response_model=SupportTicketOut,
    status_code=status.HTTP_201_CREATED,
)
def create_support_ticket(
    payload: SupportTicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    validate_order_reference(payload.order_id, current_user, db)
    audience = payload.audience or role_audience(current_user)
    if current_user.role != UserRole.ADMIN and audience != role_audience(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Support audience does not match your account role",
        )

    ticket = SupportTicket(
        requester_id=current_user.id,
        order_id=payload.order_id,
        audience=audience,
        category=payload.category,
        subject=payload.subject.strip(),
        message=payload.message.strip(),
    )
    db.add(ticket)
    db.commit()
    saved_ticket = db.scalar(
        select(SupportTicket).options(*ticket_options()).where(SupportTicket.id == ticket.id)
    )
    assert saved_ticket is not None
    return serialize_ticket(saved_ticket)


@router.get("/support/tickets", response_model=list[SupportTicketOut])
def list_my_support_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    tickets = db.scalars(
        select(SupportTicket)
        .options(*ticket_options())
        .where(SupportTicket.requester_id == current_user.id)
        .order_by(SupportTicket.created_at.desc(), SupportTicket.id.desc())
    ).all()
    return [serialize_ticket(ticket) for ticket in tickets]


@router.get("/admin/support/tickets", response_model=list[SupportTicketOut])
def list_all_support_tickets(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    tickets = db.scalars(
        select(SupportTicket)
        .options(*ticket_options())
        .order_by(SupportTicket.created_at.desc(), SupportTicket.id.desc())
    ).all()
    return [serialize_ticket(ticket) for ticket in tickets]


@router.patch("/admin/support/tickets/{ticket_id}", response_model=SupportTicketOut)
def update_support_ticket(
    ticket_id: int,
    payload: SupportTicketUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    ticket = db.scalar(
        select(SupportTicket).options(*ticket_options()).where(SupportTicket.id == ticket_id)
    )
    if ticket is None:
        raise HTTPException(status_code=404, detail="Support ticket not found")

    if payload.status is not None:
        ticket.status = payload.status
    if payload.priority is not None:
        ticket.priority = payload.priority
    if payload.resolution is not None:
        ticket.resolution = payload.resolution.strip() or None

    db.commit()
    saved_ticket = db.scalar(
        select(SupportTicket).options(*ticket_options()).where(SupportTicket.id == ticket_id)
    )
    assert saved_ticket is not None
    return serialize_ticket(saved_ticket)

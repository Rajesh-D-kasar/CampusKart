from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Order, User, WalletTransaction


def paise_to_rupees(value: int) -> float:
    return value / 100


def wallet_balance_paise(user_id: int, db: Session) -> int:
    return (
        db.scalar(
            select(func.coalesce(func.sum(WalletTransaction.amount_paise), 0)).where(
                WalletTransaction.user_id == user_id
            )
        )
        or 0
    )


def record_wallet_transaction(
    db: Session,
    *,
    user: User,
    amount_paise: int,
    transaction_type: str,
    description: str,
    order: Order | None = None,
    reference: str | None = None,
    metadata: dict | None = None,
) -> WalletTransaction | None:
    if amount_paise <= 0:
        return None
    if reference:
        existing = db.scalar(
            select(WalletTransaction).where(WalletTransaction.reference == reference)
        )
        if existing is not None:
            return existing

    balance_after = wallet_balance_paise(user.id, db) + amount_paise
    transaction = WalletTransaction(
        user_id=user.id,
        order_id=order.id if order else None,
        transaction_type=transaction_type,
        amount_paise=amount_paise,
        balance_after_paise=balance_after,
        description=description,
        reference=reference,
        metadata_json=metadata or {},
    )
    db.add(transaction)
    return transaction


def serialize_wallet_transaction(transaction: WalletTransaction) -> dict:
    return {
        "id": transaction.id,
        "order_id": transaction.order_id,
        "order_number": transaction.order.order_number if transaction.order else None,
        "transaction_type": transaction.transaction_type,
        "amount": paise_to_rupees(transaction.amount_paise),
        "balance_after": paise_to_rupees(transaction.balance_after_paise),
        "description": transaction.description,
        "reference": transaction.reference,
        "created_at": transaction.created_at,
    }

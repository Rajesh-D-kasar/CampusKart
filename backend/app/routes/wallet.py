from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import User, WalletTransaction
from app.schemas import WalletOut
from app.wallet import (
    paise_to_rupees,
    serialize_wallet_transaction,
    wallet_balance_paise,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("", response_model=WalletOut)
def read_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    transactions = db.scalars(
        select(WalletTransaction)
        .options(selectinload(WalletTransaction.order))
        .where(WalletTransaction.user_id == current_user.id)
        .order_by(WalletTransaction.created_at.desc(), WalletTransaction.id.desc())
        .limit(50)
    ).all()
    return {
        "balance": paise_to_rupees(wallet_balance_paise(current_user.id, db)),
        "transactions": [
            serialize_wallet_transaction(transaction)
            for transaction in transactions
        ],
    }

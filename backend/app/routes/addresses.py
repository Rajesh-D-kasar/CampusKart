from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Address, User
from app.schemas import AddressCreate, AddressOut, AddressUpdate

router = APIRouter(prefix="/addresses", tags=["addresses"])


def unset_default_addresses(user_id: int, db: Session) -> None:
    for address in db.scalars(select(Address).where(Address.user_id == user_id)):
        address.is_default = False


def get_owned_address(address_id: int, user_id: int, db: Session) -> Address:
    address = db.scalar(
        select(Address).where(Address.id == address_id, Address.user_id == user_id)
    )
    if address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


@router.get("", response_model=list[AddressOut])
def list_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Address]:
    return list(
        db.scalars(
            select(Address)
            .where(Address.user_id == current_user.id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        ).all()
    )


@router.post("", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def create_address(
    payload: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Address:
    has_address = db.scalar(
        select(Address.id).where(Address.user_id == current_user.id).limit(1)
    )
    should_be_default = payload.is_default or has_address is None

    if should_be_default:
        unset_default_addresses(current_user.id, db)

    address = Address(
        user_id=current_user.id,
        **payload.model_dump(exclude={"is_default"}),
        is_default=should_be_default,
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.patch("/{address_id}", response_model=AddressOut)
def update_address(
    address_id: int,
    payload: AddressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Address:
    address = get_owned_address(address_id, current_user.id, db)
    update_data = payload.model_dump(exclude_unset=True)

    if update_data.get("is_default"):
        unset_default_addresses(current_user.id, db)

    for field, value in update_data.items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return address


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    address = get_owned_address(address_id, current_user.id, db)
    db.delete(address)
    db.commit()

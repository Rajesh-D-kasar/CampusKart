from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.config import Settings, get_settings
from app.database import get_db
from app.models import Cart, User
from app.schemas import AuthToken, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def normalize_email(email: str) -> str:
    return email.strip().lower()


def token_response(user: User, settings: Settings) -> AuthToken:
    return AuthToken(
        access_token=create_access_token(str(user.id), settings=settings),
        user=user,
    )


@router.post("/register", response_model=AuthToken, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthToken:
    email = normalize_email(payload.email)
    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        phone=payload.phone.strip() if payload.phone else None,
    )
    user.cart = Cart()
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or phone already exists",
        ) from None

    db.refresh(user)
    return token_response(user, settings)


@router.post("/login", response_model=AuthToken)
def login_user(
    payload: UserLogin,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthToken:
    user = db.scalar(select(User).where(User.email == normalize_email(payload.email)))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return token_response(user, settings)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

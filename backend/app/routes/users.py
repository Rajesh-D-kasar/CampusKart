from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
import hashlib
import hmac
import secrets
import smtplib

from fastapi import APIRouter, Depends, HTTPException, Request, status
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
from app.models import AuthOtpCode, Cart, User, UserRole
from app.schemas import (
    AuthToken,
    OtpRequest,
    OtpRequestOut,
    OtpVerify,
    UserCreate,
    UserLogin,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def normalize_email(email: str) -> str:
    return email.strip().lower()


def now_utc() -> datetime:
    return datetime.now(UTC)


def ensure_aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def normalize_phone(phone: str | None) -> str | None:
    return phone.strip() if phone else None


def fallback_customer_name(email: str) -> str:
    local_part = email.split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
    return local_part.title() or "CampusKart Customer"


def hash_otp(email: str, otp: str, settings: Settings) -> str:
    message = f"{normalize_email(email)}:{otp}".encode("utf-8")
    secret = settings.jwt_secret_key.encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def latest_active_otp(email: str, db: Session) -> AuthOtpCode | None:
    return db.scalar(
        select(AuthOtpCode)
        .where(AuthOtpCode.email == email, AuthOtpCode.consumed_at.is_(None))
        .order_by(AuthOtpCode.created_at.desc(), AuthOtpCode.id.desc())
    )


def should_expose_otp(settings: Settings) -> bool:
    return settings.environment.lower() in {"development", "test", "local"}


def deliver_otp(email: str, otp: str, settings: Settings) -> None:
    if not settings.smtp_host:
        if should_expose_otp(settings):
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OTP delivery provider is not configured",
        )

    message = EmailMessage()
    message["Subject"] = "Your CampusKart login OTP"
    message["From"] = settings.otp_email_from
    message["To"] = email
    message.set_content(
        "\n".join(
            [
                "Your CampusKart login OTP is:",
                "",
                otp,
                "",
                f"This OTP expires in {settings.otp_expire_minutes} minutes.",
                "If you did not request this, you can ignore this email.",
            ]
        )
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send OTP. Please try again.",
        ) from error


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


@router.post("/otp/request", response_model=OtpRequestOut)
def request_login_otp(
    payload: OtpRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    email = normalize_email(payload.email)
    current_time = now_utc()
    existing_otp = latest_active_otp(email, db)

    if existing_otp is not None:
        resend_available_at = ensure_aware(existing_otp.resend_available_at)
        if current_time < resend_available_at:
            retry_seconds = max(
                1,
                round((resend_available_at - current_time).total_seconds()),
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {retry_seconds} seconds before requesting another OTP",
            )
        existing_otp.consumed_at = current_time

    otp = generate_otp()
    expires_at = current_time + timedelta(minutes=settings.otp_expire_minutes)
    resend_available_at = current_time + timedelta(
        seconds=settings.otp_resend_cooldown_seconds
    )
    otp_record = AuthOtpCode(
        email=email,
        code_hash=hash_otp(email, otp, settings),
        expires_at=expires_at,
        resend_available_at=resend_available_at,
        max_attempts=settings.otp_max_attempts,
        request_ip=request.client.host if request.client else None,
        user_agent=(request.headers.get("user-agent") or "")[:255] or None,
    )
    db.add(otp_record)
    deliver_otp(email, otp, settings)
    db.commit()

    return {
        "email": email,
        "expires_in_seconds": settings.otp_expire_minutes * 60,
        "resend_after_seconds": settings.otp_resend_cooldown_seconds,
        "delivery_channel": "email",
        "message": f"OTP sent. Use it within {settings.otp_expire_minutes} minutes.",
        "development_otp": otp if should_expose_otp(settings) else None,
    }


@router.post("/otp/verify", response_model=AuthToken)
def verify_login_otp(
    payload: OtpVerify,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthToken:
    email = normalize_email(payload.email)
    current_time = now_utc()
    otp_record = latest_active_otp(email, db)

    if otp_record is None:
        raise HTTPException(status_code=400, detail="OTP not found or already used")

    if current_time > ensure_aware(otp_record.expires_at):
        otp_record.consumed_at = current_time
        db.commit()
        raise HTTPException(status_code=400, detail="OTP has expired")

    if otp_record.attempts >= otp_record.max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect OTP attempts. Request a new OTP.",
        )

    otp_record.attempts += 1
    if not hmac.compare_digest(
        otp_record.code_hash,
        hash_otp(email, payload.otp, settings),
    ):
        db.commit()
        raise HTTPException(status_code=400, detail="Incorrect OTP")

    user = db.scalar(select(User).where(User.email == email))
    if user is not None and user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OTP login is available for customer accounts only",
        )

    if user is None:
        user = User(
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            full_name=(payload.full_name or fallback_customer_name(email)).strip(),
            phone=normalize_phone(payload.phone),
        )
        user.cart = Cart()
        db.add(user)
    else:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )
        if payload.full_name:
            user.full_name = payload.full_name.strip()
        if payload.phone and not user.phone:
            user.phone = normalize_phone(payload.phone)
        if user.cart is None:
            user.cart = Cart()

    otp_record.consumed_at = current_time

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


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

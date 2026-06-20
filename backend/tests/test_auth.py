from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import verify_password
from app.models import AuthOtpCode, Cart, User


def register_payload(email: str = "new-user@example.com") -> dict[str, str]:
    return {
        "email": email,
        "password": "strong-password-123",
        "full_name": "New User",
        "phone": "9876543210",
    }


def test_register_creates_user_cart_and_token(client, db_session: Session) -> None:
    response = client.post("/auth/register", json=register_payload())
    body = response.json()

    assert response.status_code == 201
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "new-user@example.com"

    user = db_session.scalar(select(User).where(User.email == "new-user@example.com"))
    assert user is not None
    assert user.password_hash != "strong-password-123"
    assert verify_password("strong-password-123", user.password_hash)
    assert db_session.scalar(select(Cart).where(Cart.user_id == user.id)) is not None


def test_register_rejects_duplicate_email(client) -> None:
    payload = register_payload()

    assert client.post("/auth/register", json=payload).status_code == 201
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json() == {"detail": "Email is already registered"}


def test_login_and_me_flow(client) -> None:
    payload = register_payload(email="login-user@example.com")
    client.post("/auth/register", json=payload)

    login_response = client.post(
        "/auth/login",
        json={"email": "login-user@example.com", "password": payload["password"]},
    )
    token = login_response.json()["access_token"]
    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert login_response.status_code == 200
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "login-user@example.com"


def test_login_rejects_wrong_password(client) -> None:
    payload = register_payload(email="wrong-password@example.com")
    client.post("/auth/register", json=payload)

    response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": "not-the-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


def test_me_rejects_invalid_token(client) -> None:
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_otp_flow_creates_customer_and_token(client, db_session: Session) -> None:
    request_response = client.post(
        "/auth/otp/request",
        json={
            "email": "otp-user@example.com",
            "full_name": "OTP User",
            "phone": "9000090000",
        },
    )
    otp = request_response.json()["development_otp"]
    verify_response = client.post(
        "/auth/otp/verify",
        json={
            "email": "otp-user@example.com",
            "otp": otp,
            "full_name": "OTP User",
            "phone": "9000090000",
        },
    )
    body = verify_response.json()
    user = db_session.scalar(select(User).where(User.email == "otp-user@example.com"))
    otp_record = db_session.scalar(
        select(AuthOtpCode).where(AuthOtpCode.email == "otp-user@example.com")
    )

    assert request_response.status_code == 200
    assert len(otp) == 6
    assert body["access_token"]
    assert body["user"]["email"] == "otp-user@example.com"
    assert user is not None
    assert user.full_name == "OTP User"
    assert db_session.scalar(select(Cart).where(Cart.user_id == user.id)) is not None
    assert otp_record is not None
    assert otp_record.consumed_at is not None


def test_otp_rejects_wrong_code_and_blocks_reuse(client) -> None:
    request_response = client.post(
        "/auth/otp/request",
        json={"email": "wrong-otp@example.com", "full_name": "Wrong OTP"},
    )
    otp = request_response.json()["development_otp"]
    wrong_otp = "000001" if otp == "000000" else "000000"

    wrong = client.post(
        "/auth/otp/verify",
        json={"email": "wrong-otp@example.com", "otp": wrong_otp},
    )
    correct = client.post(
        "/auth/otp/verify",
        json={"email": "wrong-otp@example.com", "otp": otp},
    )
    reuse = client.post(
        "/auth/otp/verify",
        json={"email": "wrong-otp@example.com", "otp": otp},
    )

    assert wrong.status_code == 400
    assert wrong.json()["detail"] == "Incorrect OTP"
    assert correct.status_code == 200
    assert reuse.status_code == 400
    assert reuse.json()["detail"] == "OTP not found or already used"


def test_otp_request_has_resend_cooldown(client) -> None:
    payload = {"email": "cooldown@example.com", "full_name": "Cool Down"}

    first = client.post("/auth/otp/request", json=payload)
    second = client.post("/auth/otp/request", json=payload)

    assert first.status_code == 200
    assert second.status_code == 429
    assert "Please wait" in second.json()["detail"]


def test_otp_login_is_customer_only(client) -> None:
    request_response = client.post(
        "/auth/otp/request",
        json={"email": "admin@campuskart.com"},
    )
    otp = request_response.json()["development_otp"]
    verify = client.post(
        "/auth/otp/verify",
        json={"email": "admin@campuskart.com", "otp": otp},
    )

    assert verify.status_code == 403
    assert verify.json()["detail"] == "OTP login is available for customer accounts only"

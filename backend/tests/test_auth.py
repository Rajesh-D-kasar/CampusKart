from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import verify_password
from app.models import Cart, User


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

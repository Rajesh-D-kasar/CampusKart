import hashlib
import hmac

from app.config import Settings, get_settings
from app.main import app


def configured_settings(secret: str = "test_secret"):
    return Settings(
        jwt_secret_key="test-jwt-secret-for-payments-1234567890",
        razorpay_key_id="rzp_test_123",
        razorpay_key_secret=secret,
    )


def missing_payment_settings():
    return Settings(jwt_secret_key="test-jwt-secret-for-payments-1234567890")


def auth_headers(client, email: str = "payments@example.com") -> dict[str, str]:
    payload = {
        "email": email,
        "password": "strong-password-123",
        "full_name": "Payment User",
        "phone": "7555555555",
    }
    response = client.post("/auth/register", json=payload)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_razorpay_order_requires_credentials(client) -> None:
    app.dependency_overrides[get_settings] = missing_payment_settings
    try:
        headers = auth_headers(client)
        response = client.post(
            "/payments/razorpay/orders",
            json={"amount": 149.5, "receipt": "order-1"},
            headers=headers,
        )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 503
    assert response.json()["detail"] == "Razorpay credentials are not configured"


def test_razorpay_signature_verification(client) -> None:
    secret = "razorpay-secret"
    app.dependency_overrides[get_settings] = lambda: configured_settings(secret)
    try:
        headers = auth_headers(client, email="verify-payment@example.com")
        order_id = "order_test_123"
        payment_id = "pay_test_456"
        signature = hmac.new(
            secret.encode("utf-8"),
            f"{order_id}|{payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        verified = client.post(
            "/payments/razorpay/verify",
            json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            },
            headers=headers,
        )
        rejected = client.post(
            "/payments/razorpay/verify",
            json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": "bad-signature-value-12345",
            },
            headers=headers,
        )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert verified.status_code == 200
    assert verified.json() == {"provider": "razorpay", "verified": True}
    assert rejected.status_code == 200
    assert rejected.json() == {"provider": "razorpay", "verified": False}

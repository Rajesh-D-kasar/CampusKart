import hashlib
import hmac
import json

from sqlalchemy import select

from app.config import Settings, get_settings
from app.main import app
from app.models import PaymentTransaction, Product
from app.seed import ADMIN_USER


def configured_settings(secret: str = "test_secret", webhook_secret: str = "webhook_secret"):
    return Settings(
        jwt_secret_key="test-jwt-secret-for-payments-1234567890",
        razorpay_key_id="rzp_test_123",
        razorpay_key_secret=secret,
        razorpay_webhook_secret=webhook_secret,
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


def login_headers(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def address_payload() -> dict[str, str | bool]:
    return {
        "label": "Hostel",
        "receiver_name": "Payment User",
        "phone": "8222222222",
        "line1": "Payment test address",
        "city": "Pune",
        "state": "Maharashtra",
        "postal_code": "411001",
        "is_default": True,
    }


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


def test_razorpay_order_and_webhook_record_payment_history(client, db_session) -> None:
    secret = "razorpay-secret"
    webhook_secret = "razorpay-webhook"
    app.dependency_overrides[get_settings] = lambda: configured_settings(
        secret,
        webhook_secret,
    )
    try:
        headers = auth_headers(client, email="razorpay-order@example.com")
        product = db_session.scalar(select(Product).order_by(Product.id))
        assert product is not None
        address = client.post("/addresses", json=address_payload(), headers=headers)
        client.post(
            "/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers=headers,
        )
        razorpay_order_id = "order_checkout_123"
        razorpay_payment_id = "pay_checkout_456"
        checkout_signature = hmac.new(
            secret.encode("utf-8"),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        order = client.post(
            "/orders",
            json={
                "address_id": address.json()["id"],
                "payment_method": "razorpay",
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": checkout_signature,
            },
            headers=headers,
        )
        webhook_body = json.dumps(
            {
                "event": "payment.captured",
                "payload": {
                    "payment": {
                        "entity": {
                            "id": razorpay_payment_id,
                            "order_id": razorpay_order_id,
                            "amount": round(order.json()["total"] * 100),
                            "currency": "INR",
                            "status": "captured",
                        }
                    }
                },
            },
            separators=(",", ":"),
        ).encode("utf-8")
        webhook_signature = hmac.new(
            webhook_secret.encode("utf-8"),
            webhook_body,
            hashlib.sha256,
        ).hexdigest()
        webhook = client.post(
            "/payments/razorpay/webhook",
            content=webhook_body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": webhook_signature,
            },
        )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    transactions = db_session.scalars(select(PaymentTransaction)).all()
    assert order.status_code == 201
    assert order.json()["payment_method"] == "razorpay"
    assert order.json()["payment_status"] == "paid"
    assert webhook.status_code == 200
    assert webhook.json()["payment_status"] == "paid"
    assert len(transactions) == 2
    assert {transaction.event_type for transaction in transactions} == {
        "order_paid",
        "payment.captured",
    }


def test_admin_can_execute_razorpay_refund(client, db_session, monkeypatch) -> None:
    secret = "razorpay-secret"
    app.dependency_overrides[get_settings] = lambda: configured_settings(secret)

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps(
                {
                    "id": "rfnd_test_789",
                    "payment_id": "pay_refund_456",
                    "amount": 12500,
                    "currency": "INR",
                    "status": "processed",
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        assert timeout == 10
        assert request.full_url.endswith("/v1/payments/pay_refund_456/refund")
        return FakeResponse()

    monkeypatch.setattr("app.routes.payments.urlopen", fake_urlopen)

    try:
        headers = auth_headers(client, email="razorpay-refund@example.com")
        product = db_session.scalar(select(Product).order_by(Product.id))
        assert product is not None
        address = client.post("/addresses", json=address_payload(), headers=headers)
        client.post(
            "/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers=headers,
        )
        razorpay_order_id = "order_refund_123"
        razorpay_payment_id = "pay_refund_456"
        checkout_signature = hmac.new(
            secret.encode("utf-8"),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        order = client.post(
            "/orders",
            json={
                "address_id": address.json()["id"],
                "payment_method": "razorpay",
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": checkout_signature,
            },
            headers=headers,
        )
        admin = login_headers(client, ADMIN_USER["email"], ADMIN_USER["password"])
        refund = client.post(
            "/payments/razorpay/refunds",
            json={"order_id": order.json()["id"], "amount": 125, "reason": "Test refund"},
            headers=admin,
        )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    transactions = db_session.scalars(
        select(PaymentTransaction).where(
            PaymentTransaction.order_id == order.json()["id"]
        )
    ).all()
    assert refund.status_code == 200
    assert refund.json()["refund_id"] == "rfnd_test_789"
    assert refund.json()["payment_status"] == "refunded"
    assert {transaction.event_type for transaction in transactions} == {
        "order_paid",
        "refund_requested",
    }

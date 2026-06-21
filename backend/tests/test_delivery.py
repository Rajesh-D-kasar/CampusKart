from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Order, PaymentStatus, Product
from app.seed import ADMIN_USER, DELIVERY_USERS
from app.tracking import assigned_partner_email


def login_headers(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def customer_headers(client, email: str = "delivery-customer@example.com") -> dict[str, str]:
    payload = {
        "email": email,
        "password": "strong-password-123",
        "full_name": "Delivery Test Customer",
        "phone": f"71{abs(hash(email)) % 10_000_000:07d}",
    }
    response = client.post("/auth/register", json=payload)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def address_payload() -> dict[str, str | bool]:
    return {
        "label": "Hostel",
        "receiver_name": "Delivery Test Customer",
        "phone": "8222222222",
        "line1": "Room 7, Main Hostel",
        "city": "Pune",
        "state": "Maharashtra",
        "postal_code": "411001",
        "is_default": True,
    }


def place_confirmed_order(
    client, db_session: Session, email: str
) -> tuple[Order, dict[str, str]]:
    customer = customer_headers(client, email=email)
    product = db_session.scalar(select(Product).order_by(Product.id))
    assert product is not None
    address = client.post("/addresses", json=address_payload(), headers=customer)
    client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers=customer,
    )
    order_response = client.post(
        "/orders",
        json={"address_id": address.json()["id"]},
        headers=customer,
    )
    admin = login_headers(client, ADMIN_USER["email"], ADMIN_USER["password"])
    client.patch(
        f"/admin/orders/{order_response.json()['id']}/status",
        json={"status": "confirmed"},
        headers=admin,
    )
    order = db_session.scalar(
        select(Order).where(Order.id == order_response.json()["id"])
    )
    assert order is not None
    db_session.refresh(order)
    return order, customer


def pickup_otp_for_order(client, order_id: int) -> str:
    admin = login_headers(client, ADMIN_USER["email"], ADMIN_USER["password"])
    ready = client.patch(f"/admin/orders/{order_id}/ready", headers=admin)
    assert ready.status_code == 200
    orders = client.get("/admin/orders", headers=admin)
    assert orders.status_code == 200
    order = next(item for item in orders.json() if item["id"] == order_id)
    assert order["store_ready"] is True
    assert order["pickup_otp"]
    assert order["items"]
    assert order["delivery_partner"] is not None
    return order["pickup_otp"]


def customer_delivery_otp_for_order(
    client, order_id: int, customer: dict[str, str]
) -> str:
    detail = client.get(f"/orders/{order_id}", headers=customer)
    assert detail.status_code == 200
    otp = detail.json()["customer_delivery_otp"]
    assert otp
    return otp


def delivery_headers_for_order(client, order: Order) -> dict[str, str]:
    email = assigned_partner_email(order)
    assert email is not None
    return login_headers(client, email, "DeliveryPass123")


def test_delivery_partner_can_list_and_complete_assigned_order(
    client, db_session: Session
) -> None:
    order, customer = place_confirmed_order(
        client, db_session, "delivery-flow@example.com"
    )
    headers = delivery_headers_for_order(client, order)
    pickup_otp = pickup_otp_for_order(client, order.id)

    listed = client.get("/delivery/orders", headers=headers)
    summary_before = client.get("/delivery/summary", headers=headers)
    out_for_delivery = client.patch(
        f"/delivery/orders/{order.id}/status",
        json={"status": "out_for_delivery", "otp": pickup_otp},
        headers=headers,
    )
    location = client.post(
        f"/delivery/orders/{order.id}/location",
        json={
            "latitude": 18.5204,
            "longitude": 73.8567,
            "accuracy_meters": 12.5,
            "battery_percent": 82,
        },
        headers=headers,
    )
    customer_otp = customer_delivery_otp_for_order(client, order.id, customer)
    delivered = client.patch(
        f"/delivery/orders/{order.id}/status",
        json={"status": "delivered", "otp": customer_otp},
        headers=headers,
    )
    summary_after = client.get("/delivery/summary", headers=headers)
    db_session.refresh(order)

    assert listed.status_code == 200
    assert any(item["id"] == order.id for item in listed.json())
    assert summary_before.status_code == 200
    assert summary_before.json()["active_orders"] == 1
    assert summary_before.json()["cod_collection_due"] == listed.json()[0]["total"]
    assert out_for_delivery.json()["status"] == "out_for_delivery"
    assert out_for_delivery.json()["pickup_verified"] is True
    assert out_for_delivery.json()["dropoff_verified"] is False
    assert location.status_code == 200
    assert location.json()["latitude"] == 18.5204
    assert delivered.json()["status"] == "delivered"
    assert delivered.json()["payment_status"] == "paid"
    assert delivered.json()["dropoff_verified"] is True
    assert delivered.json()["customer_name"] == "Delivery Test Customer"
    assert delivered.json()["delivery_partner"]["phone"].startswith("+91")
    assert summary_after.json()["active_orders"] == 0
    assert summary_after.json()["delivered_orders"] == 1
    assert summary_after.json()["cod_collection_due"] == 0
    assert order.payment_status == PaymentStatus.PAID


def test_delivery_requires_shop_pickup_otp_before_starting_route(
    client, db_session: Session
) -> None:
    order, _customer = place_confirmed_order(
        client, db_session, "missing-pickup-otp@example.com"
    )
    headers = delivery_headers_for_order(client, order)

    response = client.patch(
        f"/delivery/orders/{order.id}/status",
        json={"status": "out_for_delivery"},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Pickup OTP is required"


def test_delivery_requires_customer_otp_after_pickup(
    client, db_session: Session
) -> None:
    order, _customer = place_confirmed_order(
        client, db_session, "missing-customer-otp@example.com"
    )
    headers = delivery_headers_for_order(client, order)
    pickup_otp = pickup_otp_for_order(client, order.id)
    client.patch(
        f"/delivery/orders/{order.id}/status",
        json={"status": "out_for_delivery", "otp": pickup_otp},
        headers=headers,
    )

    response = client.patch(
        f"/delivery/orders/{order.id}/status",
        json={"status": "delivered"},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Customer delivery OTP is required"


def test_delivery_routes_reject_customers(client) -> None:
    headers = customer_headers(client, email="not-delivery@example.com")

    response = client.get("/delivery/orders", headers=headers)
    summary = client.get("/delivery/summary", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Delivery partner access required"
    assert summary.status_code == 403


def test_delivery_partner_cannot_access_unassigned_order(
    client, db_session: Session
) -> None:
    order, _customer = place_confirmed_order(
        client, db_session, "wrong-partner@example.com"
    )
    assigned_email = assigned_partner_email(order)
    assert assigned_email is not None
    other_partner = next(
        partner for partner in DELIVERY_USERS if partner["email"] != assigned_email
    )
    headers = login_headers(client, other_partner["email"], other_partner["password"])

    response = client.patch(
        f"/delivery/orders/{order.id}/status",
        json={"status": "out_for_delivery"},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Delivery order not found"

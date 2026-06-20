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


def place_confirmed_order(client, db_session: Session, email: str) -> Order:
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
    return order


def delivery_headers_for_order(client, order: Order) -> dict[str, str]:
    email = assigned_partner_email(order)
    assert email is not None
    return login_headers(client, email, "DeliveryPass123")


def test_delivery_partner_can_list_and_complete_assigned_order(
    client, db_session: Session
) -> None:
    order = place_confirmed_order(client, db_session, "delivery-flow@example.com")
    headers = delivery_headers_for_order(client, order)

    listed = client.get("/delivery/orders", headers=headers)
    out_for_delivery = client.patch(
        f"/delivery/orders/{order.id}/status",
        json={"status": "out_for_delivery"},
        headers=headers,
    )
    delivered = client.patch(
        f"/delivery/orders/{order.id}/status",
        json={"status": "delivered"},
        headers=headers,
    )
    db_session.refresh(order)

    assert listed.status_code == 200
    assert any(item["id"] == order.id for item in listed.json())
    assert out_for_delivery.json()["status"] == "out_for_delivery"
    assert delivered.json()["status"] == "delivered"
    assert delivered.json()["payment_status"] == "paid"
    assert delivered.json()["customer_name"] == "Delivery Test Customer"
    assert delivered.json()["delivery_partner"]["phone"].startswith("+91")
    assert order.payment_status == PaymentStatus.PAID


def test_delivery_routes_reject_customers(client) -> None:
    headers = customer_headers(client, email="not-delivery@example.com")

    response = client.get("/delivery/orders", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Delivery partner access required"


def test_delivery_partner_cannot_access_unassigned_order(
    client, db_session: Session
) -> None:
    order = place_confirmed_order(client, db_session, "wrong-partner@example.com")
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

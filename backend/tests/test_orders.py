from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CartItem, Inventory, Product


def auth_headers(client, email: str = "order-user@example.com") -> dict[str, str]:
    phone_suffix = abs(hash(email)) % 10_000_000
    payload = {
        "email": email,
        "password": "strong-password-123",
        "full_name": "Order User",
        "phone": f"7{phone_suffix:07d}",
    }
    response = client.post("/auth/register", json=payload)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def address_payload() -> dict[str, str | bool]:
    return {
        "label": "Hostel",
        "receiver_name": "Order User",
        "phone": "8222222222",
        "line1": "Room 202, Campus Hostel",
        "line2": "Near canteen",
        "city": "Pune",
        "state": "Maharashtra",
        "postal_code": "411001",
        "is_default": True,
    }


def first_product(db_session: Session) -> Product:
    product = db_session.scalar(select(Product).order_by(Product.id))
    assert product is not None
    return product


def test_place_order_clears_cart_and_reserves_stock(client, db_session: Session) -> None:
    headers = auth_headers(client)
    product = first_product(db_session)
    inventory = db_session.scalar(
        select(Inventory).where(Inventory.product_id == product.id)
    )
    assert inventory is not None
    reserved_before = inventory.reserved_quantity

    address = client.post("/addresses", json=address_payload(), headers=headers)
    client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 2},
        headers=headers,
    )

    response = client.post(
        "/orders",
        json={
            "address_id": address.json()["id"],
            "payment_method": "cash_on_delivery",
            "delivery_instruction": "Call before delivery",
        },
        headers=headers,
    )
    order = response.json()
    cart = client.get("/cart", headers=headers).json()
    orders = client.get("/orders", headers=headers).json()
    detail = client.get(f"/orders/{order['id']}", headers=headers).json()
    db_session.refresh(inventory)

    assert response.status_code == 201
    assert order["order_number"].startswith("CK")
    assert order["item_count"] == 2
    assert order["items"][0]["product_name"] == product.name
    assert order["delivery_address_snapshot"]["line1"] == "Room 202, Campus Hostel"
    assert order["delivery_instruction"] == "Call before delivery"
    assert order["eta_minutes"] == 22
    assert order["estimated_delivery_at"] is not None
    assert order["delivery_partner"] is None
    assert order["delivery_progress_percent"] == 0
    assert order["tracking_steps"][0]["key"] == "placed"
    assert order["tracking_steps"][0]["completed"] is True
    assert order["tracking_message"]
    assert cart["items"] == []
    assert db_session.scalars(select(CartItem)).all() == []
    assert inventory.reserved_quantity == reserved_before + 2
    assert orders[0]["id"] == order["id"]
    assert orders[0]["eta_minutes"] == 22
    assert detail["order_number"] == order["order_number"]
    assert detail["tracking_steps"][-1]["key"] == "delivered"


def test_place_order_rejects_empty_cart(client) -> None:
    headers = auth_headers(client, email="empty-order@example.com")
    address = client.post("/addresses", json=address_payload(), headers=headers)

    response = client.post(
        "/orders",
        json={"address_id": address.json()["id"]},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart is empty"


def test_online_payment_success_marks_order_paid(client, db_session: Session) -> None:
    headers = auth_headers(client, email="upi-order@example.com")
    product = first_product(db_session)
    address = client.post("/addresses", json=address_payload(), headers=headers)
    client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers=headers,
    )

    response = client.post(
        "/orders",
        json={"address_id": address.json()["id"], "payment_method": "upi"},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["payment_method"] == "upi"
    assert response.json()["payment_status"] == "paid"


def test_coupon_discount_is_applied_to_order(client, db_session: Session) -> None:
    headers = auth_headers(client, email="coupon-order@example.com")
    product = first_product(db_session)
    address = client.post("/addresses", json=address_payload(), headers=headers)
    client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 2},
        headers=headers,
    )

    response = client.post(
        "/orders",
        json={"address_id": address.json()["id"], "promo_code": "CAMPUS10"},
        headers=headers,
    )
    order = response.json()

    assert response.status_code == 201
    assert order["discount"] > 0
    assert order["total"] == order["subtotal"] + order["delivery_fee"] - order["discount"]


def test_invalid_coupon_does_not_clear_cart(client, db_session: Session) -> None:
    headers = auth_headers(client, email="bad-coupon@example.com")
    product = first_product(db_session)
    address = client.post("/addresses", json=address_payload(), headers=headers)
    client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 2},
        headers=headers,
    )

    response = client.post(
        "/orders",
        json={"address_id": address.json()["id"], "promo_code": "NOPE"},
        headers=headers,
    )
    cart = client.get("/cart", headers=headers).json()

    assert response.status_code == 400
    assert cart["item_count"] == 2


def test_online_payment_failure_does_not_clear_cart(
    client, db_session: Session
) -> None:
    headers = auth_headers(client, email="failed-payment@example.com")
    product = first_product(db_session)
    address = client.post("/addresses", json=address_payload(), headers=headers)
    client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers=headers,
    )

    response = client.post(
        "/orders",
        json={
            "address_id": address.json()["id"],
            "payment_method": "card",
            "mock_payment_result": "failed",
        },
        headers=headers,
    )
    cart = client.get("/cart", headers=headers).json()

    assert response.status_code == 402
    assert "Payment failed" in response.json()["detail"]
    assert cart["item_count"] == 1


def test_place_order_rejects_another_users_address(
    client, db_session: Session
) -> None:
    first_headers = auth_headers(client, email="address-owner@example.com")
    second_headers = auth_headers(client, email="address-thief@example.com")
    address = client.post("/addresses", json=address_payload(), headers=first_headers)
    product = first_product(db_session)
    client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers=second_headers,
    )

    response = client.post(
        "/orders",
        json={"address_id": address.json()["id"]},
        headers=second_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Address not found"

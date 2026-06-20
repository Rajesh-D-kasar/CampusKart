from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Address, Product


def auth_headers(client, email: str = "cart-user@example.com") -> dict[str, str]:
    phone_suffix = abs(hash(email)) % 10_000_000
    payload = {
        "email": email,
        "password": "strong-password-123",
        "full_name": "Cart User",
        "phone": f"8{phone_suffix:07d}",
    }
    response = client.post("/auth/register", json=payload)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def first_product_id(db_session: Session) -> int:
    product = db_session.scalar(select(Product).order_by(Product.id))
    assert product is not None
    return product.id


def test_cart_add_update_remove_and_clear(client, db_session: Session) -> None:
    headers = auth_headers(client)
    product_id = first_product_id(db_session)

    add_response = client.post(
        "/cart/items",
        json={"product_id": product_id, "quantity": 2},
        headers=headers,
    )
    update_response = client.patch(
        f"/cart/items/{product_id}",
        json={"quantity": 3},
        headers=headers,
    )
    remove_response = client.delete(f"/cart/items/{product_id}", headers=headers)
    clear_response = client.delete("/cart", headers=headers)

    assert add_response.status_code == 201
    assert add_response.json()["item_count"] == 2
    assert "image_url" in add_response.json()["items"][0]
    assert update_response.json()["item_count"] == 3
    assert remove_response.json()["item_count"] == 0
    assert clear_response.json()["items"] == []


def test_cart_requires_authentication(client, db_session: Session) -> None:
    response = client.post(
        "/cart/items",
        json={"product_id": first_product_id(db_session), "quantity": 1},
    )

    assert response.status_code == 401


def test_cart_rejects_unavailable_quantity(client, db_session: Session) -> None:
    headers = auth_headers(client, email="stock-user@example.com")
    product = db_session.scalar(select(Product).order_by(Product.id))
    assert product is not None

    response = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": product.stock_quantity + 1},
        headers=headers,
    )

    assert response.status_code == 409
    assert "available" in response.json()["detail"]


def address_payload(label: str = "Hostel") -> dict[str, str | bool]:
    return {
        "label": label,
        "receiver_name": "Address User",
        "phone": "8111111111",
        "line1": "Room 101, Campus Hostel",
        "line2": "Near main gate",
        "city": "Pune",
        "state": "Maharashtra",
        "postal_code": "411001",
        "is_default": True,
    }


def test_address_crud_and_default_selection(client, db_session: Session) -> None:
    headers = auth_headers(client, email="address-user@example.com")

    first = client.post("/addresses", json=address_payload(), headers=headers)
    second_payload = address_payload(label="Library")
    second_payload["line1"] = "Library Block"
    second = client.post("/addresses", json=second_payload, headers=headers)
    second_id = second.json()["id"]
    updated = client.patch(
        f"/addresses/{second_id}",
        json={"is_default": True, "line2": "Second floor"},
        headers=headers,
    )
    addresses = client.get("/addresses", headers=headers).json()
    deleted = client.delete(f"/addresses/{first.json()['id']}", headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert updated.json()["is_default"] is True
    assert addresses[0]["id"] == second_id
    assert deleted.status_code == 204
    assert db_session.scalar(select(Address).where(Address.id == first.json()["id"])) is None


def test_address_requires_owner(client) -> None:
    first_headers = auth_headers(client, email="owner-one@example.com")
    second_headers = auth_headers(client, email="owner-two@example.com")
    address = client.post("/addresses", json=address_payload(), headers=first_headers)

    response = client.patch(
        f"/addresses/{address.json()['id']}",
        json={"label": "Wrong owner"},
        headers=second_headers,
    )

    assert response.status_code == 404

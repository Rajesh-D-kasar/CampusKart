from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, Inventory, Order, PaymentStatus, Product
from app.seed import ADMIN_USER


def login_headers(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def customer_headers(client, email: str = "admin-test-customer@example.com") -> dict[str, str]:
    payload = {
        "email": email,
        "password": "strong-password-123",
        "full_name": "Admin Test Customer",
        "phone": "7333333333",
    }
    response = client.post("/auth/register", json=payload)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def address_payload() -> dict[str, str | bool]:
    return {
        "label": "Home",
        "receiver_name": "Admin Test Customer",
        "phone": "8222222222",
        "line1": "Admin test address",
        "city": "Pune",
        "state": "Maharashtra",
        "postal_code": "411001",
        "is_default": True,
    }


def place_customer_order(client, db_session: Session) -> int:
    headers = customer_headers(client)
    product = db_session.scalar(select(Product).order_by(Product.id))
    assert product is not None
    address = client.post("/addresses", json=address_payload(), headers=headers)
    client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers=headers,
    )
    order = client.post(
        "/orders",
        json={"address_id": address.json()["id"]},
        headers=headers,
    )
    return order.json()["id"]


def test_admin_endpoints_require_admin(client) -> None:
    headers = customer_headers(client, email="not-admin@example.com")

    response = client.get("/admin/summary", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_admin_summary_and_inventory_update(client, db_session: Session) -> None:
    headers = login_headers(client, ADMIN_USER["email"], ADMIN_USER["password"])
    product = db_session.scalar(select(Product).order_by(Product.id))
    assert product is not None

    summary = client.get("/admin/summary", headers=headers)
    inventory = client.get("/admin/inventory", headers=headers)
    updated = client.patch(
        f"/admin/inventory/{product.id}",
        json={"stock_quantity": 7, "reorder_level": 9, "is_active": True},
        headers=headers,
    )
    db_inventory = db_session.scalar(
        select(Inventory).where(Inventory.product_id == product.id)
    )

    assert summary.status_code == 200
    assert summary.json()["active_products"] >= 1
    assert inventory.status_code == 200
    assert len(inventory.json()) >= 1
    assert updated.json()["stock_quantity"] == 7
    assert updated.json()["reorder_level"] == 9
    assert db_inventory is not None
    assert db_inventory.stock_quantity == 7


def test_admin_can_create_and_update_category(client, db_session: Session) -> None:
    headers = login_headers(client, ADMIN_USER["email"], ADMIN_USER["password"])

    created = client.post(
        "/admin/categories",
        json={
            "name": "Student Snacks",
            "slug": "student-snacks",
            "display_order": 30,
        },
        headers=headers,
    )
    category_id = created.json()["id"]
    updated = client.patch(
        f"/admin/categories/{category_id}",
        json={"name": "Late Night Snacks", "is_active": False},
        headers=headers,
    )
    categories = client.get("/admin/categories", headers=headers)
    db_category = db_session.scalar(
        select(Category).where(Category.slug == "student-snacks")
    )

    assert created.status_code == 201
    assert updated.json()["name"] == "Late Night Snacks"
    assert updated.json()["is_active"] is False
    assert any(category["id"] == category_id for category in categories.json())
    assert db_category is not None
    assert db_category.is_active is False


def test_admin_can_create_and_update_product(client, db_session: Session) -> None:
    headers = login_headers(client, ADMIN_USER["email"], ADMIN_USER["password"])
    category = db_session.scalar(select(Category).order_by(Category.id))
    assert category is not None

    created = client.post(
        "/admin/products",
        json={
            "category_id": category.id,
            "name": "Test Trail Mix",
            "slug": "test-trail-mix",
            "description": "A test snack pack.",
            "unit": "200 g",
            "icon": "TM",
            "price": 99,
            "mrp": 129,
            "stock_quantity": 12,
            "reorder_level": 5,
        },
        headers=headers,
    )
    product_id = created.json()["id"]
    updated = client.patch(
        f"/admin/products/{product_id}",
        json={"price": 89, "mrp": 119, "stock_quantity": 4, "is_active": True},
        headers=headers,
    )
    products = client.get("/admin/products", headers=headers)
    public_product = client.get(f"/products/{product_id}")
    db_inventory = db_session.scalar(
        select(Inventory).where(Inventory.product_id == product_id)
    )

    assert created.status_code == 201
    assert created.json()["slug"] == "test-trail-mix"
    assert updated.json()["price"] == 89
    assert updated.json()["stock_quantity"] == 4
    assert updated.json()["low_stock"] is True
    assert any(product["id"] == product_id for product in products.json())
    assert public_product.status_code == 200
    assert db_inventory is not None
    assert db_inventory.stock_quantity == 4


def test_inactive_category_hides_public_products(client, db_session: Session) -> None:
    headers = login_headers(client, ADMIN_USER["email"], ADMIN_USER["password"])
    category = client.post(
        "/admin/categories",
        json={"name": "Hidden Test Category", "slug": "hidden-test-category"},
        headers=headers,
    )
    product = client.post(
        "/admin/products",
        json={
            "category_id": category.json()["id"],
            "name": "Hidden Test Product",
            "slug": "hidden-test-product",
            "unit": "1 pack",
            "price": 50,
            "mrp": 60,
            "stock_quantity": 10,
        },
        headers=headers,
    )

    before_hide = client.get(f"/products/{product.json()['id']}")
    client.patch(
        f"/admin/categories/{category.json()['id']}",
        json={"is_active": False},
        headers=headers,
    )
    after_hide = client.get(f"/products/{product.json()['id']}")

    assert before_hide.status_code == 200
    assert after_hide.status_code == 404


def test_admin_can_update_order_status(client, db_session: Session) -> None:
    order_id = place_customer_order(client, db_session)
    headers = login_headers(client, ADMIN_USER["email"], ADMIN_USER["password"])

    response = client.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "delivered"},
        headers=headers,
    )
    orders = client.get("/admin/orders", headers=headers)
    db_order = db_session.scalar(select(Order).where(Order.id == order_id))

    assert response.status_code == 200
    assert response.json()["status"] == "delivered"
    assert response.json()["payment_status"] == "paid"
    assert response.json()["eta_minutes"] == 0
    assert response.json()["delivery_partner"] is not None
    assert response.json()["tracking_message"]
    assert orders.json()[0]["id"] == order_id
    assert orders.json()[0]["delivery_partner"]["phone"].startswith("+91")
    assert db_order is not None
    assert db_order.payment_status == PaymentStatus.PAID


def test_admin_analytics_and_item_fulfillment(client, db_session: Session) -> None:
    order_id = place_customer_order(client, db_session)
    headers = login_headers(client, ADMIN_USER["email"], ADMIN_USER["password"])
    order = client.get("/admin/orders", headers=headers).json()[0]
    item = order["items"][0]

    updated = client.patch(
        f"/admin/orders/{order_id}/items/{item['id']}",
        json={
            "fulfillment_status": "substituted",
            "packed_quantity": item["quantity"],
            "substitution_note": "Replaced with same weight fresh pack.",
        },
        headers=headers,
    )
    analytics = client.get("/admin/analytics", headers=headers)
    settlements = client.get("/admin/settlements", headers=headers)

    assert updated.status_code == 200
    assert updated.json()["items"][0]["fulfillment_status"] == "substituted"
    assert updated.json()["items"][0]["substitution_note"]
    assert analytics.status_code == 200
    assert analytics.json()["gross_revenue"] >= updated.json()["total"]
    assert analytics.json()["top_products"]
    assert settlements.status_code == 200
    assert settlements.json()["net_settlement"] >= 0


def test_admin_can_assign_delivery_partner(client, db_session: Session) -> None:
    order_id = place_customer_order(client, db_session)
    headers = login_headers(client, ADMIN_USER["email"], ADMIN_USER["password"])
    partners = client.get("/admin/delivery-partners", headers=headers)
    assert partners.status_code == 200
    partner = partners.json()[0]

    confirmed = client.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=headers,
    )
    assigned = client.patch(
        f"/admin/orders/{order_id}/assignment",
        json={"delivery_partner_id": partner["id"]},
        headers=headers,
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["delivery_partner"] is not None
    assert assigned.status_code == 200
    assert assigned.json()["delivery_partner"]["name"] == partner["name"]


def test_support_ticket_flow_for_customer_and_admin(client) -> None:
    customer = customer_headers(client, email="support-customer@example.com")
    admin = login_headers(client, ADMIN_USER["email"], ADMIN_USER["password"])

    created = client.post(
        "/support/tickets",
        json={
            "audience": "customer",
            "category": "delivery",
            "subject": "Delivery OTP issue",
            "message": "Customer did not receive the delivery OTP clearly.",
        },
        headers=customer,
    )
    mine = client.get("/support/tickets", headers=customer)
    all_tickets = client.get("/admin/support/tickets", headers=admin)
    updated = client.patch(
        f"/admin/support/tickets/{created.json()['id']}",
        json={"status": "resolved", "priority": "high", "resolution": "Customer contacted."},
        headers=admin,
    )
    reply = client.post(
        f"/support/tickets/{created.json()['id']}/messages",
        json={"message": "Support team has replied from admin desk."},
        headers=admin,
    )

    assert created.status_code == 201
    assert created.json()["status"] == "open"
    assert created.json()["messages"][0]["message"] == (
        "Customer did not receive the delivery OTP clearly."
    )
    assert mine.status_code == 200
    assert mine.json()[0]["subject"] == "Delivery OTP issue"
    assert all_tickets.status_code == 200
    assert any(ticket["id"] == created.json()["id"] for ticket in all_tickets.json())
    assert updated.json()["status"] == "resolved"
    assert updated.json()["priority"] == "high"
    assert reply.status_code == 200
    assert reply.json()["messages"][-1]["message"] == "Support team has replied from admin desk."

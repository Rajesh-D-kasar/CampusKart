from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_products_returns_catalog() -> None:
    response = client.get("/products")
    products = response.json()

    assert response.status_code == 200
    assert len(products) >= 3
    assert all(product["price"] >= 0 for product in products)


def test_get_product_returns_404_for_unknown_id() -> None:
    response = client.get("/products/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}

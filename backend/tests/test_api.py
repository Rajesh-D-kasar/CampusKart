from app.seed import CATEGORIES, PRODUCTS


def test_health_checks(client) -> None:
    response = client.get("/health")

    assert response.json() == {"status": "ok"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert client.get("/health/database").json() == {
        "status": "ok",
        "database": "reachable",
    }


def test_list_products_returns_seeded_catalog(client) -> None:
    response = client.get("/products")
    products = response.json()

    assert response.status_code == 200
    assert len(products) == len(PRODUCTS)
    assert all(product["price"] >= 0 for product in products)
    assert all(product["discount_percent"] >= 0 for product in products)
    assert all("stock_quantity" in product for product in products)
    assert any(product["image_url"] for product in products)


def test_products_support_search_and_category_filter(client) -> None:
    search_response = client.get("/products", params={"search": "milk"})
    category_response = client.get("/products", params={"category": "beverages"})

    assert [item["name"] for item in search_response.json()] == ["Milk"]
    assert {item["category_slug"] for item in category_response.json()} == {"beverages"}


def test_products_support_price_sorting(client) -> None:
    low_to_high = client.get("/products", params={"sort": "price_low"}).json()
    high_to_low = client.get("/products", params={"sort": "price_high"}).json()
    discounted = client.get("/products", params={"sort": "discount"}).json()

    assert [item["price"] for item in low_to_high] == sorted(
        item["price"] for item in low_to_high
    )
    assert [item["price"] for item in high_to_low] == sorted(
        (item["price"] for item in high_to_low),
        reverse=True,
    )
    assert discounted[0]["discount_percent"] >= discounted[-1]["discount_percent"]


def test_list_categories_returns_counts(client) -> None:
    response = client.get("/products/categories")
    categories = response.json()

    assert response.status_code == 200
    assert [category["slug"] for category in categories] == [
        category["slug"] for category in CATEGORIES
    ]
    assert sum(category["product_count"] for category in categories) == len(PRODUCTS)


def test_get_product_returns_404_for_unknown_id(client) -> None:
    response = client.get("/products/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


def test_product_recommendations_prioritize_related_items(client) -> None:
    products = client.get("/products").json()
    product = products[0]
    response = client.get(f"/products/{product['id']}/recommendations")
    recommendations = response.json()

    assert response.status_code == 200
    assert 1 <= len(recommendations) <= 8
    assert product["id"] not in {item["id"] for item in recommendations}
    same_category_products = [
        item
        for item in products
        if item["id"] != product["id"]
        and item["category_slug"] == product["category_slug"]
    ]
    if same_category_products:
        assert recommendations[0]["category_slug"] == product["category_slug"]


def test_product_recommendations_return_404_for_unknown_id(client) -> None:
    response = client.get("/products/999/recommendations")

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}

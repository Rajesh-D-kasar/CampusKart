from app.promotions import COUPONS


def test_offers_returns_banners_coupons_and_collections(client) -> None:
    response = client.get("/offers")
    offers = response.json()

    assert response.status_code == 200
    assert len(offers["banners"]) >= 1
    assert [coupon["code"] for coupon in offers["coupons"]] == [
        coupon["code"] for coupon in COUPONS
    ]
    assert {collection["key"] for collection in offers["collections"]} == {
        "top-discounts",
        "value-picks",
        "popular-essentials",
    }
    assert all(collection["products"] for collection in offers["collections"])


def test_coupon_preview_applies_percentage_discount(client) -> None:
    response = client.post(
        "/offers/coupons/preview",
        json={"code": "campus10", "subtotal": 250, "delivery_fee": 20},
    )
    preview = response.json()

    assert response.status_code == 200
    assert preview["code"] == "CAMPUS10"
    assert preview["discount"] == 25
    assert preview["total"] == 245


def test_coupon_preview_rejects_invalid_or_small_orders(client) -> None:
    invalid = client.post(
        "/offers/coupons/preview",
        json={"code": "NOPE", "subtotal": 250, "delivery_fee": 20},
    )
    small_order = client.post(
        "/offers/coupons/preview",
        json={"code": "FIRST50", "subtotal": 100, "delivery_fee": 20},
    )

    assert invalid.status_code == 400
    assert small_order.status_code == 400

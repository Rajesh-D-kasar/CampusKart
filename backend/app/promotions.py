from dataclasses import dataclass


class PromotionError(ValueError):
    pass


PROMO_BANNERS = [
    {
        "id": "campus-saver",
        "title": "Campus Saver Week",
        "subtitle": "Use CAMPUS10 for 10% off daily essentials above Rs 199.",
        "cta_label": "Shop deals",
        "cta_href": "/products?sort=price_low",
        "tone": "green",
    },
    {
        "id": "fast-breakfast",
        "title": "Breakfast in minutes",
        "subtitle": "Milk, eggs, fruits, juice, and coffee ready for quick checkout.",
        "cta_label": "Build basket",
        "cta_href": "/products?search=milk",
        "tone": "yellow",
    },
]

COUPONS = [
    {
        "code": "CAMPUS10",
        "title": "10% off",
        "description": "Get 10% off up to Rs 75 on orders above Rs 199.",
        "discount_type": "percentage",
        "discount_value": 10,
        "min_order_value": 199,
        "max_discount": 75,
    },
    {
        "code": "FIRST50",
        "title": "Rs 50 off",
        "description": "Flat Rs 50 off on first-style test orders above Rs 299.",
        "discount_type": "flat",
        "discount_value": 50,
        "min_order_value": 299,
        "max_discount": 50,
    },
    {
        "code": "FREESHIP",
        "title": "Free delivery",
        "description": "Waive delivery fee on orders above Rs 149.",
        "discount_type": "free_delivery",
        "discount_value": 0,
        "min_order_value": 149,
        "max_discount": 20,
    },
]


@dataclass(frozen=True)
class AppliedPromotion:
    code: str | None
    title: str | None
    description: str | None
    discount_paise: int
    delivery_fee_paise: int
    delivery_savings_paise: int

    @property
    def savings_paise(self) -> int:
        return self.discount_paise + self.delivery_savings_paise


def rupees_to_paise(value: int | float) -> int:
    return round(float(value) * 100)


def paise_to_rupees(value: int) -> float:
    return value / 100


def normalize_coupon_code(code: str | None) -> str | None:
    if not code:
        return None
    normalized = code.strip().upper()
    return normalized or None


def get_coupon(code: str | None) -> dict | None:
    normalized = normalize_coupon_code(code)
    if normalized is None:
        return None
    return next((coupon for coupon in COUPONS if coupon["code"] == normalized), None)


def apply_coupon(
    subtotal_paise: int,
    delivery_fee_paise: int,
    code: str | None,
) -> AppliedPromotion:
    normalized = normalize_coupon_code(code)
    if normalized is None:
        return AppliedPromotion(None, None, None, 0, delivery_fee_paise, 0)

    coupon = get_coupon(normalized)
    if coupon is None:
        raise PromotionError("Coupon code is not valid.")

    minimum_paise = rupees_to_paise(coupon["min_order_value"])
    if subtotal_paise < minimum_paise:
        remaining = paise_to_rupees(minimum_paise - subtotal_paise)
        raise PromotionError(f"Add Rs {remaining:.0f} more to use {coupon['code']}.")

    discount_paise = 0
    next_delivery_fee_paise = delivery_fee_paise
    delivery_savings_paise = 0

    if coupon["discount_type"] == "percentage":
        raw_discount = round(subtotal_paise * coupon["discount_value"] / 100)
        discount_paise = min(raw_discount, rupees_to_paise(coupon["max_discount"]))
    elif coupon["discount_type"] == "flat":
        discount_paise = min(
            subtotal_paise,
            rupees_to_paise(coupon["discount_value"]),
        )
    elif coupon["discount_type"] == "free_delivery":
        delivery_savings_paise = delivery_fee_paise
        next_delivery_fee_paise = 0

    return AppliedPromotion(
        code=coupon["code"],
        title=coupon["title"],
        description=coupon["description"],
        discount_paise=discount_paise,
        delivery_fee_paise=next_delivery_fee_paise,
        delivery_savings_paise=delivery_savings_paise,
    )

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Inventory, Product
from app.promotions import (
    COUPONS,
    PROMO_BANNERS,
    PromotionError,
    apply_coupon,
    paise_to_rupees,
    rupees_to_paise,
)
from app.schemas import CouponPreviewOut, CouponPreviewRequest, OffersOut

router = APIRouter(prefix="/offers", tags=["offers"])


def product_options():
    return (
        selectinload(Product.category),
        selectinload(Product.inventory_items).selectinload(Inventory.store),
    )


def active_products(db: Session) -> list[Product]:
    return list(
        db.scalars(
            select(Product)
            .options(*product_options())
            .where(Product.is_active.is_(True))
            .order_by(Product.name)
        ).all()
    )


def build_collections(products: list[Product]) -> list[dict]:
    in_stock_products = [product for product in products if product.in_stock]
    top_discounts = sorted(
        in_stock_products,
        key=lambda product: (product.discount_percent, product.mrp_paise),
        reverse=True,
    )[:4]
    value_picks = sorted(in_stock_products, key=lambda product: product.price_paise)[:4]
    popular_essentials = sorted(
        in_stock_products,
        key=lambda product: (
            product.category_slug in {"dairy-eggs", "beverages", "pantry"},
            product.stock_quantity,
        ),
        reverse=True,
    )[:4]

    return [
        {
            "key": "top-discounts",
            "title": "Top discounts",
            "description": "Products with the strongest markdowns in the catalog.",
            "products": top_discounts,
        },
        {
            "key": "value-picks",
            "title": "Value picks",
            "description": "Low-price essentials for quick student baskets.",
            "products": value_picks,
        },
        {
            "key": "popular-essentials",
            "title": "Popular essentials",
            "description": "High-stock everyday items for fast checkout.",
            "products": popular_essentials,
        },
    ]


@router.get("", response_model=OffersOut)
def list_offers(db: Session = Depends(get_db)) -> dict:
    return {
        "banners": PROMO_BANNERS,
        "coupons": COUPONS,
        "collections": build_collections(active_products(db)),
    }


@router.post("/coupons/preview", response_model=CouponPreviewOut)
def preview_coupon(payload: CouponPreviewRequest) -> dict:
    subtotal_paise = rupees_to_paise(payload.subtotal)
    delivery_fee_paise = rupees_to_paise(payload.delivery_fee)

    try:
        applied = apply_coupon(
            subtotal_paise=subtotal_paise,
            delivery_fee_paise=delivery_fee_paise,
            code=payload.code,
        )
    except PromotionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    total_paise = max(
        0,
        subtotal_paise + applied.delivery_fee_paise - applied.discount_paise,
    )

    return {
        "code": applied.code,
        "title": applied.title,
        "description": applied.description,
        "subtotal": payload.subtotal,
        "delivery_fee": paise_to_rupees(applied.delivery_fee_paise),
        "discount": paise_to_rupees(applied.discount_paise),
        "savings": paise_to_rupees(applied.savings_paise),
        "total": paise_to_rupees(total_paise),
    }

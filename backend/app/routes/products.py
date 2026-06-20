from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Category, Inventory, Product
from app.schemas import CategoryOut, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


def product_query():
    return select(Product).options(
        selectinload(Product.category),
        selectinload(Product.inventory_items).selectinload(Inventory.store),
    )


@router.get("", response_model=list[ProductOut])
def list_products(
    search: str | None = Query(default=None, min_length=1, max_length=100),
    category: str | None = Query(default=None, min_length=1, max_length=120),
    sort: Literal["name", "price_low", "price_high", "discount"] = "name",
    db: Session = Depends(get_db),
) -> list[Product]:
    statement = product_query().where(
        Product.is_active.is_(True),
        Product.category.has(Category.is_active.is_(True)),
    )

    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(Product.name.ilike(pattern), Product.description.ilike(pattern))
        )

    if category:
        statement = statement.where(Product.category.has(slug=category))

    if sort == "price_low":
        statement = statement.order_by(Product.price_paise, Product.name)
    elif sort == "price_high":
        statement = statement.order_by(Product.price_paise.desc(), Product.name)
    elif sort == "discount":
        discount_expression = (
            (Product.mrp_paise - Product.price_paise) * 100.0 / Product.mrp_paise
        )
        statement = statement.order_by(
            discount_expression.desc(),
            Product.name,
        )
    else:
        statement = statement.order_by(Product.name)

    return list(db.scalars(statement).all())


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)) -> list[dict[str, int | str | None]]:
    statement = (
        select(Category, func.count(Product.id).label("product_count"))
        .outerjoin(
            Product,
            and_(Product.category_id == Category.id, Product.is_active.is_(True)),
        )
        .where(Category.is_active.is_(True))
        .group_by(Category.id)
        .order_by(Category.display_order, Category.name)
    )

    return [
        {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "image_url": category.image_url,
            "display_order": category.display_order,
            "product_count": product_count,
        }
        for category, product_count in db.execute(statement).all()
    ]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    product = db.scalar(product_query().where(Product.id == product_id))
    if product is None or not product.is_active or not product.category.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

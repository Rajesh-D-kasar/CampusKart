import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_admin
from app.database import get_db
from app.models import (
    Category,
    Inventory,
    Order,
    OrderStatus,
    PaymentStatus,
    Product,
    Store,
    User,
)
from app.schemas import (
    AdminCategoryCreate,
    AdminCategoryOut,
    AdminCategoryUpdate,
    AdminInventoryOut,
    AdminInventoryUpdate,
    AdminOrderOut,
    AdminOrderStatusUpdate,
    AdminProductCreate,
    AdminProductOut,
    AdminProductUpdate,
    AdminSummaryOut,
)
from app.tracking import tracking_summary

router = APIRouter(prefix="/admin", tags=["admin"])


def paise_to_rupees(value: int) -> float:
    return value / 100


def rupees_to_paise(value: float) -> int:
    return round(value * 100)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def get_active_store(db: Session) -> Store:
    store = db.scalar(select(Store).where(Store.is_active.is_(True)).order_by(Store.id))
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No active store is available",
        )
    return store


def inventory_options():
    return (
        selectinload(Inventory.product).selectinload(Product.category),
        selectinload(Inventory.store),
    )


def order_options():
    return selectinload(Order.items), selectinload(Order.user)


def product_options():
    return (
        selectinload(Product.category),
        selectinload(Product.inventory_items).selectinload(Inventory.store),
    )


def category_options():
    return selectinload(Category.products)


def validate_product_prices(price_paise: int, mrp_paise: int) -> None:
    if mrp_paise < price_paise:
        raise HTTPException(
            status_code=400,
            detail="MRP cannot be lower than selling price",
        )


def ensure_unique_category_slug(
    slug: str,
    db: Session,
    category_id: int | None = None,
) -> None:
    existing = db.scalar(select(Category).where(Category.slug == slug))
    if existing is not None and existing.id != category_id:
        raise HTTPException(status_code=409, detail="Category slug already exists")


def ensure_unique_product_slug(
    slug: str,
    db: Session,
    product_id: int | None = None,
) -> None:
    existing = db.scalar(select(Product).where(Product.slug == slug))
    if existing is not None and existing.id != product_id:
        raise HTTPException(status_code=409, detail="Product slug already exists")


def serialize_admin_order(order: Order) -> dict:
    item_count = sum(item.quantity for item in order.items)
    snapshot = order.delivery_address_snapshot or {}
    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": enum_value(order.status),
        "payment_status": enum_value(order.payment_status),
        "payment_method": order.payment_method,
        "item_count": item_count,
        "subtotal": paise_to_rupees(order.subtotal_paise),
        "delivery_fee": paise_to_rupees(order.delivery_fee_paise),
        "discount": paise_to_rupees(order.discount_paise),
        "total": paise_to_rupees(order.total_paise),
        **tracking_summary(order),
        "created_at": order.created_at,
        "customer_name": order.user.full_name,
        "customer_email": order.user.email,
        "delivery_city": snapshot.get("city"),
    }


def serialize_admin_category(category: Category) -> dict:
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "image_url": category.image_url,
        "display_order": category.display_order,
        "is_active": category.is_active,
        "product_count": len(category.products),
    }


def inventory_for_product(product: Product, store_id: int) -> Inventory | None:
    return next(
        (item for item in product.inventory_items if item.store_id == store_id),
        None,
    )


def serialize_admin_product(product: Product, store_id: int) -> dict:
    inventory = inventory_for_product(product, store_id)
    stock_quantity = inventory.stock_quantity if inventory else 0
    reserved_quantity = inventory.reserved_quantity if inventory else 0
    reorder_level = inventory.reorder_level if inventory else 10
    available_quantity = stock_quantity - reserved_quantity

    return {
        "id": product.id,
        "category_id": product.category_id,
        "category": product.category.name,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "unit": product.unit,
        "icon": product.icon,
        "image_url": product.image_url,
        "price": product.price,
        "mrp": product.mrp,
        "discount_percent": product.discount_percent,
        "is_active": product.is_active,
        "stock_quantity": stock_quantity,
        "reserved_quantity": reserved_quantity,
        "available_quantity": available_quantity,
        "reorder_level": reorder_level,
        "low_stock": available_quantity <= reorder_level,
    }


def serialize_inventory(item: Inventory) -> dict:
    available_quantity = item.available_quantity
    return {
        "product_id": item.product_id,
        "name": item.product.name,
        "slug": item.product.slug,
        "category": item.product.category.name,
        "price": item.product.price,
        "mrp": item.product.mrp,
        "image_url": item.product.image_url,
        "is_active": item.product.is_active,
        "stock_quantity": item.stock_quantity,
        "reserved_quantity": item.reserved_quantity,
        "available_quantity": available_quantity,
        "reorder_level": item.reorder_level,
        "low_stock": available_quantity <= item.reorder_level,
    }


@router.get("/summary", response_model=AdminSummaryOut)
def read_admin_summary(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    orders = list(db.scalars(select(Order)).all())
    inventory_items = list(
        db.scalars(
            select(Inventory)
            .options(*inventory_options())
            .where(Inventory.product.has(Product.is_active.is_(True)))
        ).all()
    )
    active_products = list(
        db.scalars(select(Product).where(Product.is_active.is_(True))).all()
    )

    open_statuses = {
        OrderStatus.PLACED,
        OrderStatus.CONFIRMED,
        OrderStatus.PACKING,
        OrderStatus.OUT_FOR_DELIVERY,
    }
    paid_or_delivered_orders = [
        order for order in orders if order.status != OrderStatus.CANCELLED
    ]

    return {
        "total_orders": len(orders),
        "open_orders": sum(1 for order in orders if order.status in open_statuses),
        "active_products": len(active_products),
        "low_stock_items": sum(
            1 for item in inventory_items if item.available_quantity <= item.reorder_level
        ),
        "total_revenue": paise_to_rupees(
            sum(order.total_paise for order in paid_or_delivered_orders)
        ),
    }


@router.get("/orders", response_model=list[AdminOrderOut])
def list_admin_orders(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    orders = db.scalars(
        select(Order)
        .options(*order_options())
        .order_by(Order.created_at.desc(), Order.id.desc())
    ).all()
    return [serialize_admin_order(order) for order in orders]


@router.patch("/orders/{order_id}/status", response_model=AdminOrderOut)
def update_order_status(
    order_id: int,
    payload: AdminOrderStatusUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    order = db.scalar(
        select(Order).options(*order_options()).where(Order.id == order_id)
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = OrderStatus(payload.status)
    if order.status == OrderStatus.DELIVERED and order.payment_method == "cash_on_delivery":
        order.payment_status = PaymentStatus.PAID

    db.commit()
    db.refresh(order)
    return serialize_admin_order(order)


@router.get("/categories", response_model=list[AdminCategoryOut])
def list_admin_categories(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    categories = db.scalars(
        select(Category)
        .options(category_options())
        .order_by(Category.display_order, Category.name)
    ).all()
    return [serialize_admin_category(category) for category in categories]


@router.post(
    "/categories",
    response_model=AdminCategoryOut,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    payload: AdminCategoryCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    slug = slugify(payload.slug or payload.name)
    ensure_unique_category_slug(slug, db)

    category = Category(
        name=payload.name.strip(),
        slug=slug,
        image_url=payload.image_url or None,
        display_order=payload.display_order,
        is_active=payload.is_active,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return serialize_admin_category(category)


@router.patch("/categories/{category_id}", response_model=AdminCategoryOut)
def update_category(
    category_id: int,
    payload: AdminCategoryUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    category = db.scalar(
        select(Category)
        .options(category_options())
        .where(Category.id == category_id)
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    if payload.name is not None:
        category.name = payload.name.strip()
    if payload.slug is not None:
        slug = slugify(payload.slug)
        ensure_unique_category_slug(slug, db, category.id)
        category.slug = slug
    if payload.image_url is not None:
        category.image_url = payload.image_url or None
    if payload.display_order is not None:
        category.display_order = payload.display_order
    if payload.is_active is not None:
        category.is_active = payload.is_active

    db.commit()
    db.refresh(category)
    return serialize_admin_category(category)


@router.get("/products", response_model=list[AdminProductOut])
def list_admin_products(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    store = get_active_store(db)
    products = db.scalars(
        select(Product)
        .options(*product_options())
        .order_by(Product.name)
    ).all()
    return [serialize_admin_product(product, store.id) for product in products]


@router.post(
    "/products",
    response_model=AdminProductOut,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    payload: AdminProductCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    store = get_active_store(db)
    category = db.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    price_paise = rupees_to_paise(payload.price)
    mrp_paise = rupees_to_paise(payload.mrp)
    validate_product_prices(price_paise, mrp_paise)

    slug = slugify(payload.slug or payload.name)
    ensure_unique_product_slug(slug, db)

    product = Product(
        category_id=category.id,
        name=payload.name.strip(),
        slug=slug,
        description=payload.description,
        unit=payload.unit.strip(),
        icon=payload.icon,
        image_url=payload.image_url or None,
        price_paise=price_paise,
        mrp_paise=mrp_paise,
        is_active=payload.is_active,
    )
    db.add(product)
    db.flush()
    db.add(
        Inventory(
            store_id=store.id,
            product_id=product.id,
            stock_quantity=payload.stock_quantity,
            reorder_level=payload.reorder_level,
        )
    )
    db.commit()

    saved_product = db.scalar(
        select(Product)
        .options(*product_options())
        .where(Product.id == product.id)
    )
    assert saved_product is not None
    return serialize_admin_product(saved_product, store.id)


@router.patch("/products/{product_id}", response_model=AdminProductOut)
def update_product(
    product_id: int,
    payload: AdminProductUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    store = get_active_store(db)
    product = db.scalar(
        select(Product)
        .options(*product_options())
        .where(Product.id == product_id)
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.category_id is not None:
        category = db.get(Category, payload.category_id)
        if category is None:
            raise HTTPException(status_code=404, detail="Category not found")
        product.category_id = category.id

    if payload.name is not None:
        product.name = payload.name.strip()
    if payload.slug is not None:
        slug = slugify(payload.slug)
        ensure_unique_product_slug(slug, db, product.id)
        product.slug = slug
    if payload.description is not None:
        product.description = payload.description
    if payload.unit is not None:
        product.unit = payload.unit.strip()
    if payload.icon is not None:
        product.icon = payload.icon
    if payload.image_url is not None:
        product.image_url = payload.image_url or None
    if payload.is_active is not None:
        product.is_active = payload.is_active

    next_price_paise = (
        rupees_to_paise(payload.price)
        if payload.price is not None
        else product.price_paise
    )
    next_mrp_paise = (
        rupees_to_paise(payload.mrp)
        if payload.mrp is not None
        else product.mrp_paise
    )
    validate_product_prices(next_price_paise, next_mrp_paise)
    product.price_paise = next_price_paise
    product.mrp_paise = next_mrp_paise

    inventory = inventory_for_product(product, store.id)
    if inventory is None:
        inventory = Inventory(store_id=store.id, product_id=product.id)
        db.add(inventory)
        product.inventory_items.append(inventory)

    if payload.stock_quantity is not None:
        if payload.stock_quantity < inventory.reserved_quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stock cannot be below reserved quantity",
            )
        inventory.stock_quantity = payload.stock_quantity
    if payload.reorder_level is not None:
        inventory.reorder_level = payload.reorder_level

    db.commit()
    db.refresh(product)
    return serialize_admin_product(product, store.id)


@router.get("/inventory", response_model=list[AdminInventoryOut])
def list_inventory(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    store = get_active_store(db)
    inventory_items = db.scalars(
        select(Inventory)
        .options(*inventory_options())
        .where(
            Inventory.store_id == store.id,
            Inventory.product.has(Product.is_active.is_(True)),
        )
        .order_by(Inventory.id)
    ).all()
    return [serialize_inventory(item) for item in inventory_items]


@router.patch("/inventory/{product_id}", response_model=AdminInventoryOut)
def update_inventory(
    product_id: int,
    payload: AdminInventoryUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    store = get_active_store(db)
    inventory = db.scalar(
        select(Inventory)
        .options(*inventory_options())
        .where(Inventory.store_id == store.id, Inventory.product_id == product_id)
    )
    if inventory is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    if payload.stock_quantity is not None:
        if payload.stock_quantity < inventory.reserved_quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stock cannot be below reserved quantity",
            )
        inventory.stock_quantity = payload.stock_quantity

    if payload.reorder_level is not None:
        inventory.reorder_level = payload.reorder_level

    if payload.is_active is not None:
        inventory.product.is_active = payload.is_active

    db.commit()
    db.refresh(inventory)
    return serialize_inventory(inventory)

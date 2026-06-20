from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Cart, CartItem, Inventory, Product, User
from app.schemas import CartItemCreate, CartItemUpdate, CartOut

router = APIRouter(prefix="/cart", tags=["cart"])

DELIVERY_FEE_PAISE = 2000
FREE_DELIVERY_THRESHOLD_PAISE = 19900


def paise_to_rupees(value: int) -> float:
    return value / 100


def product_options():
    return (
        selectinload(CartItem.product)
        .selectinload(Product.inventory_items)
        .selectinload(Inventory.store)
    )


def get_or_create_cart(user: User, db: Session) -> Cart:
    cart = db.scalar(
        select(Cart)
        .options(selectinload(Cart.items).options(product_options()))
        .where(Cart.user_id == user.id)
        .execution_options(populate_existing=True)
    )

    if cart is not None:
        return cart

    cart = Cart(user_id=user.id)
    db.add(cart)
    db.flush()
    return cart


def get_product(product_id: int, db: Session) -> Product:
    product = db.scalar(
        select(Product)
        .options(selectinload(Product.inventory_items).selectinload(Inventory.store))
        .where(Product.id == product_id)
    )

    if product is None or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def validate_quantity(product: Product, quantity: int) -> None:
    if not product.in_stock:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is out of stock",
        )
    if quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only {product.stock_quantity} item(s) available",
        )


def serialize_cart(cart: Cart) -> CartOut:
    items = []
    subtotal_paise = 0
    item_count = 0

    for item in sorted(cart.items, key=lambda cart_item: cart_item.product.name):
        line_total_paise = item.product.price_paise * item.quantity
        subtotal_paise += line_total_paise
        item_count += item.quantity
        items.append(
            {
                "id": item.id,
                "product_id": item.product_id,
                "name": item.product.name,
                "slug": item.product.slug,
                "unit": item.product.unit,
                "icon": item.product.icon,
                "image_url": item.product.image_url,
                "price": item.product.price,
                "mrp": item.product.mrp,
                "quantity": item.quantity,
                "line_total": paise_to_rupees(line_total_paise),
                "stock_quantity": item.product.stock_quantity,
                "in_stock": item.product.in_stock,
            }
        )

    delivery_fee_paise = (
        0
        if subtotal_paise == 0 or subtotal_paise >= FREE_DELIVERY_THRESHOLD_PAISE
        else DELIVERY_FEE_PAISE
    )

    return CartOut(
        items=items,
        item_count=item_count,
        subtotal=paise_to_rupees(subtotal_paise),
        delivery_fee=paise_to_rupees(delivery_fee_paise),
        total=paise_to_rupees(subtotal_paise + delivery_fee_paise),
    )


@router.get("", response_model=CartOut)
def read_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartOut:
    return serialize_cart(get_or_create_cart(current_user, db))


@router.post("/items", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_cart_item(
    payload: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartOut:
    cart = get_or_create_cart(current_user, db)
    product = get_product(payload.product_id, db)
    existing_item = next(
        (item for item in cart.items if item.product_id == product.id),
        None,
    )
    next_quantity = payload.quantity + (existing_item.quantity if existing_item else 0)
    validate_quantity(product, next_quantity)

    if existing_item:
        existing_item.quantity = next_quantity
    else:
        cart.items.append(CartItem(product_id=product.id, quantity=payload.quantity))

    db.commit()
    db.refresh(cart)
    return serialize_cart(get_or_create_cart(current_user, db))


@router.patch("/items/{product_id}", response_model=CartOut)
def update_cart_item(
    product_id: int,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartOut:
    cart = get_or_create_cart(current_user, db)
    item = next(
        (cart_item for cart_item in cart.items if cart_item.product_id == product_id),
        None,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")

    validate_quantity(item.product, payload.quantity)
    item.quantity = payload.quantity
    db.commit()
    return serialize_cart(get_or_create_cart(current_user, db))


@router.delete("/items/{product_id}", response_model=CartOut)
def remove_cart_item(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartOut:
    cart = get_or_create_cart(current_user, db)
    item = next(
        (cart_item for cart_item in cart.items if cart_item.product_id == product_id),
        None,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(item)
    db.commit()
    return serialize_cart(get_or_create_cart(current_user, db))


@router.delete("", response_model=CartOut)
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartOut:
    cart = get_or_create_cart(current_user, db)

    for item in list(cart.items):
        db.delete(item)

    db.commit()
    return serialize_cart(get_or_create_cart(current_user, db))

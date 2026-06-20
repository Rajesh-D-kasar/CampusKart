from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Address,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Product,
    Store,
    User,
)


def test_customer_cart_and_order_relationships(db_session: Session) -> None:
    product = db_session.scalar(select(Product).where(Product.slug == "milk-1l"))
    store = db_session.scalar(
        select(Store).where(Store.slug == "campuskart-central")
    )
    assert product is not None
    assert store is not None

    user = User(
        email="customer@example.com",
        password_hash="future-auth-step",
        full_name="Test Customer",
        phone="9999999999",
    )
    address = Address(
        user=user,
        label="Hostel",
        receiver_name=user.full_name,
        phone=user.phone,
        line1="Room 101, Campus Hostel",
        city="Pune",
        state="Maharashtra",
        postal_code="411001",
        is_default=True,
    )
    cart = Cart(user=user)
    cart.items.append(CartItem(product=product, quantity=2))
    order = Order(
        order_number="CKTEST0001",
        user=user,
        store=store,
        address=address,
        delivery_address_snapshot={
            "receiver_name": user.full_name,
            "phone": user.phone,
            "line1": address.line1,
            "city": address.city,
            "state": address.state,
            "postal_code": address.postal_code,
        },
        subtotal_paise=product.price_paise * 2,
        delivery_fee_paise=2000,
        total_paise=(product.price_paise * 2) + 2000,
    )
    order.items.append(
        OrderItem(
            product=product,
            product_name=product.name,
            unit=product.unit,
            unit_price_paise=product.price_paise,
            quantity=2,
            line_total_paise=product.price_paise * 2,
        )
    )
    db_session.add(user)
    db_session.commit()

    assert user.cart is cart
    assert cart.items[0].product.name == "Milk"
    assert order.items[0].line_total_paise == product.price_paise * 2
    assert user.orders[0].address.label == "Hostel"

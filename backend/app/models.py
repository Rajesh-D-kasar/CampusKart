from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    DELIVERY_PARTNER = "delivery_partner"


class OrderStatus(str, Enum):
    PLACED = "placed"
    CONFIRMED = "confirmed"
    PACKING = "packing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


def enum_values(enum_class):
    return [member.value for member in enum_class]


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(
            UserRole,
            create_constraint=True,
            native_enum=False,
            length=32,
            values_callable=enum_values,
        ),
        default=UserRole.CUSTOMER,
        server_default=UserRole.CUSTOMER.value,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    addresses: Mapped[list["Address"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    cart: Mapped[Optional["Cart"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    orders: Mapped[list["Order"]] = relationship(
        back_populates="user", foreign_keys="Order.user_id"
    )


class AuthOtpCode(TimestampMixin, Base):
    __tablename__ = "auth_otp_codes"
    __table_args__ = (
        Index("ix_auth_otp_email_created", "email", "created_at"),
        Index("ix_auth_otp_email_consumed", "email", "consumed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    code_hash: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    resend_available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, server_default="5")
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    request_ip: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))


class Address(TimestampMixin, Base):
    __tablename__ = "addresses"
    __table_args__ = (
        Index("ix_addresses_user_default", "user_id", "is_default"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(40), default="Home")
    receiver_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    line1: Mapped[str] = mapped_column(String(255))
    line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(12), index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6))
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    user: Mapped["User"] = relationship(back_populates="addresses")
    orders: Mapped[list["Order"]] = relationship(back_populates="address")


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Store(TimestampMixin, Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    line1: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(12), index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6))
    service_radius_km: Mapped[int] = mapped_column(
        Integer, default=5, server_default="5"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    inventory_items: Mapped[list["Inventory"]] = relationship(
        back_populates="store", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="store")


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price_paise >= 0", name="price_non_negative"),
        CheckConstraint("mrp_paise >= price_paise", name="mrp_not_below_price"),
        Index("ix_products_category_active", "category_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(180), index=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(80))
    icon: Mapped[str] = mapped_column(String(20), default="")
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    price_paise: Mapped[int] = mapped_column(Integer)
    mrp_paise: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    category: Mapped["Category"] = relationship(back_populates="products")
    inventory_items: Mapped[list["Inventory"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="product")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")

    @property
    def price(self) -> float:
        return self.price_paise / 100

    @property
    def mrp(self) -> float:
        return self.mrp_paise / 100

    @property
    def discount_percent(self) -> int:
        if self.mrp_paise <= self.price_paise:
            return 0
        return round(((self.mrp_paise - self.price_paise) / self.mrp_paise) * 100)

    @property
    def category_name(self) -> str:
        return self.category.name

    @property
    def category_slug(self) -> str:
        return self.category.slug

    @property
    def stock_quantity(self) -> int:
        return sum(
            item.available_quantity
            for item in self.inventory_items
            if item.store.is_active
        )

    @property
    def in_stock(self) -> bool:
        return self.is_active and self.stock_quantity > 0


class Inventory(TimestampMixin, Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("store_id", "product_id"),
        CheckConstraint("stock_quantity >= 0", name="stock_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="reserved_non_negative"),
        CheckConstraint(
            "reserved_quantity <= stock_quantity", name="reserved_within_stock"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    reserved_quantity: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    reorder_level: Mapped[int] = mapped_column(Integer, default=10, server_default="10")

    store: Mapped["Store"] = relationship(back_populates="inventory_items")
    product: Mapped["Product"] = relationship(back_populates="inventory_items")

    @property
    def available_quantity(self) -> int:
        return self.stock_quantity - self.reserved_quantity


class Cart(TimestampMixin, Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )

    user: Mapped["User"] = relationship(back_populates="cart")
    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(TimestampMixin, Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "product_id"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, server_default="1")

    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="cart_items")


class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("subtotal_paise >= 0", name="subtotal_non_negative"),
        CheckConstraint("delivery_fee_paise >= 0", name="delivery_fee_non_negative"),
        CheckConstraint("discount_paise >= 0", name="discount_non_negative"),
        CheckConstraint("total_paise >= 0", name="total_non_negative"),
        Index("ix_orders_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    assigned_delivery_partner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="RESTRICT"), index=True
    )
    address_id: Mapped[int] = mapped_column(
        ForeignKey("addresses.id", ondelete="RESTRICT"), index=True
    )
    delivery_address_snapshot: Mapped[dict[str, str]] = mapped_column(JSON)
    status: Mapped[OrderStatus] = mapped_column(
        SqlEnum(
            OrderStatus,
            create_constraint=True,
            native_enum=False,
            length=32,
            values_callable=enum_values,
        ),
        default=OrderStatus.PLACED,
        server_default=OrderStatus.PLACED.value,
        index=True,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SqlEnum(
            PaymentStatus,
            create_constraint=True,
            native_enum=False,
            length=32,
            values_callable=enum_values,
        ),
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )
    payment_method: Mapped[str] = mapped_column(
        String(30), default="cash_on_delivery"
    )
    subtotal_paise: Mapped[int] = mapped_column(Integer)
    delivery_fee_paise: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    discount_paise: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    total_paise: Mapped[int] = mapped_column(Integer)
    delivery_instruction: Mapped[Optional[str]] = mapped_column(String(300))

    user: Mapped["User"] = relationship(back_populates="orders", foreign_keys=[user_id])
    assigned_delivery_partner: Mapped[Optional["User"]] = relationship(
        foreign_keys=[assigned_delivery_partner_id]
    )
    store: Mapped["Store"] = relationship(back_populates="orders")
    address: Mapped["Address"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    handoff_verification: Mapped[Optional["OrderHandoffVerification"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", uselist=False
    )
    payment_transactions: Mapped[list["PaymentTransaction"]] = relationship(
        back_populates="order"
    )
    notifications: Mapped[list["Notification"]] = relationship(back_populates="order")
    delivery_locations: Mapped[list["DeliveryLocation"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderHandoffVerification(TimestampMixin, Base):
    __tablename__ = "order_handoff_verifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), unique=True, index=True
    )
    pickup_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    dropoff_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    store_ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    pickup_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    dropoff_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, server_default="5")

    order: Mapped["Order"] = relationship(back_populates="handoff_verification")


class OrderItem(TimestampMixin, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price_paise >= 0", name="unit_price_non_negative"),
        CheckConstraint("line_total_paise >= 0", name="line_total_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), index=True
    )
    product_name: Mapped[str] = mapped_column(String(180))
    unit: Mapped[str] = mapped_column(String(80))
    unit_price_paise: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    line_total_paise: Mapped[int] = mapped_column(Integer)
    packed_quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    fulfillment_status: Mapped[str] = mapped_column(
        String(30), default="pending", server_default="pending", index=True
    )
    substitution_note: Mapped[Optional[str]] = mapped_column(String(255))

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped[Optional["Product"]] = relationship(back_populates="order_items")


class PaymentTransaction(TimestampMixin, Base):
    __tablename__ = "payment_transactions"
    __table_args__ = (
        Index("ix_payment_transactions_order_created", "order_id", "created_at"),
        Index("ix_payment_transactions_provider_order", "provider", "provider_order_id"),
        Index(
            "ix_payment_transactions_provider_payment",
            "provider",
            "provider_payment_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    provider: Mapped[str] = mapped_column(String(40), default="razorpay")
    provider_order_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    provider_payment_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    provider_refund_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    amount_paise: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR")
    verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    signature: Mapped[Optional[str]] = mapped_column(String(255))
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON)

    order: Mapped[Optional["Order"]] = relationship(back_populates="payment_transactions")
    user: Mapped[Optional["User"]] = relationship(foreign_keys=[user_id])


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), index=True
    )
    channel: Mapped[str] = mapped_column(String(30), default="in_app")
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(140))
    message: Mapped[str] = mapped_column(String(500))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    order: Mapped[Optional["Order"]] = relationship(back_populates="notifications")


class DeliveryLocation(TimestampMixin, Base):
    __tablename__ = "delivery_locations"
    __table_args__ = (
        Index("ix_delivery_locations_order_created", "order_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    delivery_partner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    latitude: Mapped[float] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float] = mapped_column(Numeric(9, 6))
    accuracy_meters: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    battery_percent: Mapped[Optional[int]] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(40), default="browser")

    order: Mapped["Order"] = relationship(back_populates="delivery_locations")
    delivery_partner: Mapped["User"] = relationship(foreign_keys=[delivery_partner_id])


class SupportTicket(TimestampMixin, Base):
    __tablename__ = "support_tickets"
    __table_args__ = (
        Index("ix_support_tickets_requester_created", "requester_id", "created_at"),
        Index("ix_support_tickets_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), index=True
    )
    audience: Mapped[str] = mapped_column(String(30), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    subject: Mapped[str] = mapped_column(String(140))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="open", server_default="open")
    priority: Mapped[str] = mapped_column(
        String(30), default="normal", server_default="normal"
    )
    resolution: Mapped[Optional[str]] = mapped_column(Text)

    requester: Mapped["User"] = relationship(foreign_keys=[requester_id])
    order: Mapped[Optional["Order"]] = relationship(foreign_keys=[order_id])
    messages: Mapped[list["SupportTicketMessage"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="SupportTicketMessage.id",
    )


class SupportTicketMessage(TimestampMixin, Base):
    __tablename__ = "support_ticket_messages"
    __table_args__ = (
        Index("ix_support_ticket_messages_ticket_created", "ticket_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("support_tickets.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    message: Mapped[str] = mapped_column(Text)
    is_internal: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    ticket: Mapped["SupportTicket"] = relationship(back_populates="messages")
    author: Mapped["User"] = relationship(foreign_keys=[author_id])

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    price: float = Field(ge=0)
    mrp: float = Field(ge=0)
    category: str = Field(validation_alias="category_name")
    category_slug: str
    unit: str
    icon: str
    image_url: str | None
    discount_percent: int = Field(ge=0)
    in_stock: bool
    stock_quantity: int = Field(ge=0)


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    image_url: str | None = None
    display_order: int = Field(ge=0)
    product_count: int = Field(ge=0)


class PromoBannerOut(BaseModel):
    id: str
    title: str
    subtitle: str
    cta_label: str
    cta_href: str
    tone: str


class CouponOut(BaseModel):
    code: str
    title: str
    description: str
    discount_type: str
    discount_value: float = Field(ge=0)
    min_order_value: float = Field(ge=0)
    max_discount: float = Field(ge=0)


class CouponPreviewRequest(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    subtotal: float = Field(ge=0)
    delivery_fee: float = Field(ge=0)


class CouponPreviewOut(BaseModel):
    code: str
    title: str
    description: str
    subtotal: float = Field(ge=0)
    delivery_fee: float = Field(ge=0)
    discount: float = Field(ge=0)
    savings: float = Field(ge=0)
    total: float = Field(ge=0)


class ProductCollectionOut(BaseModel):
    key: str
    title: str
    description: str
    products: list[ProductOut]


class OffersOut(BaseModel):
    banners: list[PromoBannerOut]
    coupons: list[CouponOut]
    collections: list[ProductCollectionOut]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = Field(default=None, min_length=7, max_length=20)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    phone: str | None
    role: str
    is_active: bool
    created_at: datetime


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class OtpRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, min_length=7, max_length=20)


class OtpRequestOut(BaseModel):
    email: EmailStr
    expires_in_seconds: int = Field(gt=0)
    resend_after_seconds: int = Field(ge=0)
    delivery_channel: str = "email"
    message: str
    development_otp: str | None = None


class OtpVerify(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, min_length=7, max_length=20)


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=99)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=99)


class CartItemOut(BaseModel):
    id: int
    product_id: int
    name: str
    slug: str
    unit: str
    icon: str
    image_url: str | None = None
    price: float = Field(ge=0)
    mrp: float = Field(ge=0)
    quantity: int = Field(ge=1)
    line_total: float = Field(ge=0)
    stock_quantity: int = Field(ge=0)
    in_stock: bool


class CartOut(BaseModel):
    items: list[CartItemOut]
    item_count: int = Field(ge=0)
    subtotal: float = Field(ge=0)
    delivery_fee: float = Field(ge=0)
    total: float = Field(ge=0)


class AddressBase(BaseModel):
    label: str = Field(default="Home", min_length=1, max_length=40)
    receiver_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=20)
    line1: str = Field(min_length=5, max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=4, max_length=12)
    latitude: float | None = None
    longitude: float | None = None
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=40)
    receiver_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, min_length=7, max_length=20)
    line1: str | None = Field(default=None, min_length=5, max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    postal_code: str | None = Field(default=None, min_length=4, max_length=12)
    latitude: float | None = None
    longitude: float | None = None
    is_default: bool | None = None


class AddressOut(AddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class OrderCreate(BaseModel):
    address_id: int
    payment_method: Literal["cash_on_delivery", "upi", "card"] = "cash_on_delivery"
    mock_payment_result: Literal["success", "failed"] = "success"
    promo_code: str | None = Field(default=None, max_length=30)
    delivery_instruction: str | None = Field(default=None, max_length=300)


class OrderItemOut(BaseModel):
    id: int
    product_id: int | None
    product_name: str
    unit: str
    unit_price: float = Field(ge=0)
    quantity: int = Field(ge=1)
    line_total: float = Field(ge=0)


class DeliveryPartnerOut(BaseModel):
    name: str
    phone: str
    vehicle_number: str


class OrderTrackingStepOut(BaseModel):
    key: str
    label: str
    description: str
    completed: bool
    current: bool
    timestamp: datetime | None = None


class OrderSummaryOut(BaseModel):
    id: int
    order_number: str
    status: str
    payment_status: str
    payment_method: str
    item_count: int = Field(ge=0)
    subtotal: float = Field(ge=0)
    delivery_fee: float = Field(ge=0)
    discount: float = Field(ge=0)
    total: float = Field(ge=0)
    eta_minutes: int | None = Field(default=None, ge=0)
    estimated_delivery_at: datetime | None = None
    delivery_partner: DeliveryPartnerOut | None = None
    tracking_message: str
    created_at: datetime


class OrderOut(OrderSummaryOut):
    address_id: int
    delivery_address_snapshot: dict[str, str | None]
    delivery_instruction: str | None
    items: list[OrderItemOut]
    delivery_progress_percent: int = Field(ge=0, le=100)
    tracking_steps: list[OrderTrackingStepOut]
    updated_at: datetime


class DeliveryOrderOut(OrderOut):
    customer_name: str
    customer_email: EmailStr
    customer_phone: str | None
    delivery_city: str | None


class DeliveryOrderStatusUpdate(BaseModel):
    status: Literal["out_for_delivery", "delivered"]


class DeliverySummaryOut(BaseModel):
    active_orders: int = Field(ge=0)
    packing_orders: int = Field(ge=0)
    out_for_delivery_orders: int = Field(ge=0)
    delivered_orders: int = Field(ge=0)
    cod_collection_due: float = Field(ge=0)
    delivered_value: float = Field(ge=0)


class RazorpayOrderCreate(BaseModel):
    amount: float = Field(gt=0, le=500_000)
    currency: str = Field(default="INR", min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    receipt: str | None = Field(default=None, max_length=40)
    notes: dict[str, str] | None = None


class RazorpayOrderOut(BaseModel):
    provider: str = "razorpay"
    order_id: str
    amount: float = Field(gt=0)
    currency: str
    key_id: str


class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str = Field(min_length=1, max_length=100)
    razorpay_payment_id: str = Field(min_length=1, max_length=100)
    razorpay_signature: str = Field(min_length=20, max_length=200)


class RazorpayVerifyOut(BaseModel):
    provider: str = "razorpay"
    verified: bool


class AdminSummaryOut(BaseModel):
    total_orders: int = Field(ge=0)
    open_orders: int = Field(ge=0)
    active_products: int = Field(ge=0)
    low_stock_items: int = Field(ge=0)
    total_revenue: float = Field(ge=0)


class AdminOrderOut(OrderSummaryOut):
    customer_name: str
    customer_email: EmailStr
    delivery_city: str | None


class AdminOrderStatusUpdate(BaseModel):
    status: Literal[
        "placed",
        "confirmed",
        "packing",
        "out_for_delivery",
        "delivered",
        "cancelled",
    ]


class AdminInventoryOut(BaseModel):
    product_id: int
    name: str
    slug: str
    category: str
    price: float = Field(ge=0)
    mrp: float = Field(ge=0)
    image_url: str | None
    is_active: bool
    stock_quantity: int = Field(ge=0)
    reserved_quantity: int = Field(ge=0)
    available_quantity: int = Field(ge=0)
    reorder_level: int = Field(ge=0)
    low_stock: bool


class AdminInventoryUpdate(BaseModel):
    stock_quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class AdminCategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    image_url: str | None = None
    display_order: int = Field(ge=0)
    is_active: bool
    product_count: int = Field(ge=0)


class AdminCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str | None = Field(default=None, min_length=2, max_length=120)
    image_url: str | None = Field(default=None, max_length=500)
    display_order: int = Field(default=0, ge=0)
    is_active: bool = True


class AdminCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    slug: str | None = Field(default=None, min_length=2, max_length=120)
    image_url: str | None = Field(default=None, max_length=500)
    display_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class AdminProductOut(BaseModel):
    id: int
    category_id: int
    category: str
    name: str
    slug: str
    description: str | None
    unit: str
    icon: str
    image_url: str | None
    price: float = Field(ge=0)
    mrp: float = Field(ge=0)
    discount_percent: int = Field(ge=0)
    is_active: bool
    stock_quantity: int = Field(ge=0)
    reserved_quantity: int = Field(ge=0)
    available_quantity: int = Field(ge=0)
    reorder_level: int = Field(ge=0)
    low_stock: bool


class AdminProductCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=2, max_length=180)
    slug: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    unit: str = Field(min_length=1, max_length=80)
    icon: str = Field(default="", max_length=20)
    image_url: str | None = Field(default=None, max_length=500)
    price: float = Field(ge=0)
    mrp: float = Field(ge=0)
    is_active: bool = True
    stock_quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=10, ge=0)


class AdminProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=180)
    slug: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=80)
    icon: str | None = Field(default=None, max_length=20)
    image_url: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, ge=0)
    mrp: float | None = Field(default=None, ge=0)
    is_active: bool | None = None
    stock_quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)

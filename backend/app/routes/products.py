from fastapi import APIRouter, HTTPException

from app.schemas import Product

router = APIRouter(prefix="/products", tags=["products"])

PRODUCTS = [
    Product(
        id=1,
        name="Maggi Noodles",
        price=15,
        category="Snacks",
        unit="70 g pack",
        icon="🍜",
    ),
    Product(
        id=2,
        name="Fresh Milk",
        price=60,
        category="Dairy",
        unit="1 litre",
        icon="🥛",
    ),
    Product(
        id=3,
        name="Whole Wheat Bread",
        price=40,
        category="Bakery",
        unit="400 g loaf",
        icon="🍞",
    ),
    Product(
        id=4,
        name="Bananas",
        price=45,
        category="Fruits",
        unit="6 pieces",
        icon="🍌",
    ),
    Product(
        id=5,
        name="Potato Chips",
        price=20,
        category="Snacks",
        unit="52 g pack",
        icon="🥔",
    ),
    Product(
        id=6,
        name="Orange Juice",
        price=110,
        category="Beverages",
        unit="1 litre",
        icon="🧃",
    ),
    Product(
        id=7,
        name="Eggs",
        price=78,
        category="Breakfast",
        unit="6 pieces",
        icon="🥚",
    ),
    Product(
        id=8,
        name="Dark Chocolate",
        price=95,
        category="Sweets",
        unit="100 g bar",
        icon="🍫",
    ),
]


@router.get("", response_model=list[Product])
def list_products() -> list[Product]:
    return PRODUCTS


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: int) -> Product:
    product = next((item for item in PRODUCTS if item.id == product_id), None)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

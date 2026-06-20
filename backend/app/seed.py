from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.database import SessionLocal
from app.models import Category, Inventory, Product, Store, User, UserRole

DEFAULT_STORE = {
    "name": "CampusKart Central Store",
    "slug": "campuskart-central",
    "line1": "Main Campus Road",
    "city": "Pune",
    "state": "Maharashtra",
    "postal_code": "411001",
    "service_radius_km": 5,
}

ADMIN_USER = {
    "email": "admin@campuskart.com",
    "password": "AdminPass123",
    "full_name": "CampusKart Admin",
    "phone": "9000000000",
}

DELIVERY_USERS = [
    {
        "email": "delivery1@campuskart.com",
        "password": "DeliveryPass123",
        "full_name": "Aman Delivery",
        "phone": "9000011101",
    },
    {
        "email": "delivery2@campuskart.com",
        "password": "DeliveryPass123",
        "full_name": "Rohit Runner",
        "phone": "9000011102",
    },
    {
        "email": "delivery3@campuskart.com",
        "password": "DeliveryPass123",
        "full_name": "Priya Express",
        "phone": "9000011103",
    },
]

CATEGORIES = [
    {"name": "Fruits", "slug": "fruits", "display_order": 1},
    {"name": "Vegetables", "slug": "vegetables", "display_order": 2},
    {"name": "Dairy & Eggs", "slug": "dairy-eggs", "display_order": 3},
    {"name": "Beverages", "slug": "beverages", "display_order": 4},
    {"name": "Pantry", "slug": "pantry", "display_order": 5},
    {"name": "Meat & Seafood", "slug": "meat-seafood", "display_order": 6},
    {"name": "Frozen & Desserts", "slug": "frozen-desserts", "display_order": 7},
    {"name": "Pet Care", "slug": "pet-care", "display_order": 8},
    {"name": "Household", "slug": "household", "display_order": 9},
    {"name": "Health & Nutrition", "slug": "health-nutrition", "display_order": 10},
]

# Product names/images are adapted from DummyJSON's public grocery sample data
# for testing and prototyping. INR prices/MRPs are synthetic for this app.
PRODUCTS = [
    {
        "name": "Apple",
        "slug": "apple",
        "category_slug": "fruits",
        "description": "Fresh everyday apples for snacks, salads, and lunch boxes.",
        "unit": "4 pieces",
        "icon": "\U0001f34e",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/apple/thumbnail.webp",
        "price_paise": 12000,
        "mrp_paise": 14000,
        "stock_quantity": 48,
    },
    {
        "name": "Bananas",
        "slug": "bananas-6-pieces",
        "category_slug": "fruits",
        "description": "Ripe bananas for quick breakfast and smoothies.",
        "unit": "6 pieces",
        "icon": "\U0001f34c",
        "image_url": None,
        "price_paise": 4500,
        "mrp_paise": 5000,
        "stock_quantity": 60,
    },
    {
        "name": "Kiwi",
        "slug": "kiwi",
        "category_slug": "fruits",
        "description": "Tangy imported-style kiwi for fruit bowls.",
        "unit": "3 pieces",
        "icon": "\U0001f95d",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/kiwi/thumbnail.webp",
        "price_paise": 14900,
        "mrp_paise": 17500,
        "stock_quantity": 42,
    },
    {
        "name": "Strawberry",
        "slug": "strawberry",
        "category_slug": "fruits",
        "description": "Fresh strawberries for desserts and shakes.",
        "unit": "200 g pack",
        "icon": "\U0001f353",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/strawberry/thumbnail.webp",
        "price_paise": 17900,
        "mrp_paise": 21000,
        "stock_quantity": 34,
    },
    {
        "name": "Lemon",
        "slug": "lemon",
        "category_slug": "fruits",
        "description": "Juicy lemons for drinks, salads, and cooking.",
        "unit": "4 pieces",
        "icon": "\U0001f34b",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/lemon/thumbnail.webp",
        "price_paise": 3900,
        "mrp_paise": 4500,
        "stock_quantity": 55,
    },
    {
        "name": "Mulberry",
        "slug": "mulberry",
        "category_slug": "fruits",
        "description": "Sweet mulberries for snacking and toppings.",
        "unit": "125 g pack",
        "icon": "\U0001fad0",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/mulberry/thumbnail.webp",
        "price_paise": 19900,
        "mrp_paise": 23000,
        "stock_quantity": 30,
    },
    {
        "name": "Cucumber",
        "slug": "cucumber",
        "category_slug": "vegetables",
        "description": "Crunchy cucumbers for salads and sandwiches.",
        "unit": "500 g",
        "icon": "\U0001f952",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/cucumber/thumbnail.webp",
        "price_paise": 3500,
        "mrp_paise": 4200,
        "stock_quantity": 70,
    },
    {
        "name": "Potatoes",
        "slug": "potatoes",
        "category_slug": "vegetables",
        "description": "Fresh potatoes for curries, fries, and snacks.",
        "unit": "1 kg",
        "icon": "\U0001f954",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/potatoes/thumbnail.webp",
        "price_paise": 4900,
        "mrp_paise": 6000,
        "stock_quantity": 90,
    },
    {
        "name": "Red Onions",
        "slug": "red-onions",
        "category_slug": "vegetables",
        "description": "Kitchen-staple red onions.",
        "unit": "1 kg",
        "icon": "\U0001f9c5",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/red-onions/thumbnail.webp",
        "price_paise": 5500,
        "mrp_paise": 6500,
        "stock_quantity": 85,
    },
    {
        "name": "Green Bell Pepper",
        "slug": "green-bell-pepper",
        "category_slug": "vegetables",
        "description": "Green bell peppers for stir fry, pizza, and sandwiches.",
        "unit": "250 g",
        "icon": "\U0001fad1",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/green-bell-pepper/thumbnail.webp",
        "price_paise": 6500,
        "mrp_paise": 7500,
        "stock_quantity": 40,
    },
    {
        "name": "Green Chili Pepper",
        "slug": "green-chili-pepper",
        "category_slug": "vegetables",
        "description": "Spicy green chillies for Indian cooking.",
        "unit": "100 g",
        "icon": "\U0001f336",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/green-chili-pepper/thumbnail.webp",
        "price_paise": 2500,
        "mrp_paise": 3000,
        "stock_quantity": 35,
    },
    {
        "name": "Milk",
        "slug": "milk-1l",
        "category_slug": "dairy-eggs",
        "description": "Daily milk pack for tea, coffee, and breakfast.",
        "unit": "1 litre",
        "icon": "\U0001f95b",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/milk/thumbnail.webp",
        "price_paise": 6000,
        "mrp_paise": 6500,
        "stock_quantity": 52,
    },
    {
        "name": "Eggs",
        "slug": "eggs-12-pieces",
        "category_slug": "dairy-eggs",
        "description": "Protein-rich eggs for breakfast and baking.",
        "unit": "12 pieces",
        "icon": "\U0001f95a",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/eggs/thumbnail.webp",
        "price_paise": 8400,
        "mrp_paise": 9600,
        "stock_quantity": 44,
    },
    {
        "name": "Juice",
        "slug": "juice-1l",
        "category_slug": "beverages",
        "description": "Fruit juice for breakfast and evening refreshment.",
        "unit": "1 litre",
        "icon": "\U0001f9c3",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/juice/thumbnail.webp",
        "price_paise": 12000,
        "mrp_paise": 14500,
        "stock_quantity": 45,
    },
    {
        "name": "Soft Drinks",
        "slug": "soft-drinks",
        "category_slug": "beverages",
        "description": "Chilled soft drinks for quick refreshment.",
        "unit": "750 ml",
        "icon": "\U0001f964",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/soft-drinks/thumbnail.webp",
        "price_paise": 4000,
        "mrp_paise": 4500,
        "stock_quantity": 80,
    },
    {
        "name": "Water",
        "slug": "water-1l",
        "category_slug": "beverages",
        "description": "Packaged drinking water bottle.",
        "unit": "1 litre",
        "icon": "\U0001f4a7",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/water/thumbnail.webp",
        "price_paise": 2000,
        "mrp_paise": 2500,
        "stock_quantity": 100,
    },
    {
        "name": "Nescafe Coffee",
        "slug": "nescafe-coffee",
        "category_slug": "beverages",
        "description": "Instant coffee for quick campus caffeine.",
        "unit": "100 g jar",
        "icon": "\U00002615",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/nescafe-coffee/thumbnail.webp",
        "price_paise": 26000,
        "mrp_paise": 29900,
        "stock_quantity": 38,
    },
    {
        "name": "Cooking Oil",
        "slug": "cooking-oil-1l",
        "category_slug": "pantry",
        "description": "Everyday cooking oil for home kitchens.",
        "unit": "1 litre",
        "icon": "\U0001f6e2",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/cooking-oil/thumbnail.webp",
        "price_paise": 16500,
        "mrp_paise": 19000,
        "stock_quantity": 46,
    },
    {
        "name": "Rice",
        "slug": "rice-5kg",
        "category_slug": "pantry",
        "description": "Daily-use rice pack for meals.",
        "unit": "5 kg bag",
        "icon": "\U0001f35a",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/rice/thumbnail.webp",
        "price_paise": 39900,
        "mrp_paise": 45000,
        "stock_quantity": 50,
    },
    {
        "name": "Honey Jar",
        "slug": "honey-jar",
        "category_slug": "pantry",
        "description": "Honey jar for tea, toast, and desserts.",
        "unit": "500 g jar",
        "icon": "\U0001f36f",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/honey-jar/thumbnail.webp",
        "price_paise": 22000,
        "mrp_paise": 25000,
        "stock_quantity": 33,
    },
    {
        "name": "Chicken Meat",
        "slug": "chicken-meat",
        "category_slug": "meat-seafood",
        "description": "Fresh chicken meat for curries and grilling.",
        "unit": "500 g",
        "icon": "\U0001f357",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/chicken-meat/thumbnail.webp",
        "price_paise": 26000,
        "mrp_paise": 30000,
        "stock_quantity": 28,
    },
    {
        "name": "Fish Steak",
        "slug": "fish-steak",
        "category_slug": "meat-seafood",
        "description": "Fish steak cuts for pan-fry and curry.",
        "unit": "500 g",
        "icon": "\U0001f41f",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/fish-steak/thumbnail.webp",
        "price_paise": 34900,
        "mrp_paise": 39900,
        "stock_quantity": 24,
    },
    {
        "name": "Ice Cream",
        "slug": "ice-cream",
        "category_slug": "frozen-desserts",
        "description": "Creamy ice cream for dessert cravings.",
        "unit": "500 ml tub",
        "icon": "\U0001f368",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/ice-cream/thumbnail.webp",
        "price_paise": 14900,
        "mrp_paise": 18000,
        "stock_quantity": 34,
    },
    {
        "name": "Cat Food",
        "slug": "cat-food",
        "category_slug": "pet-care",
        "description": "Dry cat food for daily feeding.",
        "unit": "1 kg pack",
        "icon": "\U0001f431",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/cat-food/thumbnail.webp",
        "price_paise": 24900,
        "mrp_paise": 29900,
        "stock_quantity": 32,
    },
    {
        "name": "Dog Food",
        "slug": "dog-food",
        "category_slug": "pet-care",
        "description": "Dry dog food for daily meals.",
        "unit": "1 kg pack",
        "icon": "\U0001f436",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/dog-food/thumbnail.webp",
        "price_paise": 29900,
        "mrp_paise": 34900,
        "stock_quantity": 36,
    },
    {
        "name": "Tissue Paper Box",
        "slug": "tissue-paper-box",
        "category_slug": "household",
        "description": "Soft tissue paper box for home and desk.",
        "unit": "100 pulls",
        "icon": "\U0001f9fb",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/tissue-paper-box/thumbnail.webp",
        "price_paise": 7900,
        "mrp_paise": 9500,
        "stock_quantity": 60,
    },
    {
        "name": "Protein Powder",
        "slug": "protein-powder",
        "category_slug": "health-nutrition",
        "description": "Protein powder for post-workout shakes.",
        "unit": "1 kg jar",
        "icon": "\U0001f4aa",
        "image_url": "https://cdn.dummyjson.com/product-images/groceries/protein-powder/thumbnail.webp",
        "price_paise": 89900,
        "mrp_paise": 99900,
        "stock_quantity": 20,
    },
]


def seed_catalog(db: Session) -> None:
    admin = db.scalar(select(User).where(User.email == ADMIN_USER["email"]))
    if admin is None:
        admin = db.scalar(select(User).where(User.phone == ADMIN_USER["phone"]))
    if admin is None:
        admin = User(
            email=ADMIN_USER["email"],
            password_hash=hash_password(ADMIN_USER["password"]),
            full_name=ADMIN_USER["full_name"],
            phone=ADMIN_USER["phone"],
            role=UserRole.ADMIN,
        )
        db.add(admin)
    else:
        admin.email = ADMIN_USER["email"]
        admin.full_name = ADMIN_USER["full_name"]
        admin.phone = ADMIN_USER["phone"]
        admin.password_hash = hash_password(ADMIN_USER["password"])
        admin.role = UserRole.ADMIN
        admin.is_active = True

    for delivery_data in DELIVERY_USERS:
        delivery_user = db.scalar(
            select(User).where(User.email == delivery_data["email"])
        )
        if delivery_user is None:
            delivery_user = db.scalar(
                select(User).where(User.phone == delivery_data["phone"])
            )
        if delivery_user is None:
            delivery_user = User(
                email=delivery_data["email"],
                password_hash=hash_password(delivery_data["password"]),
                full_name=delivery_data["full_name"],
                phone=delivery_data["phone"],
                role=UserRole.DELIVERY_PARTNER,
            )
            db.add(delivery_user)
        else:
            delivery_user.email = delivery_data["email"]
            delivery_user.full_name = delivery_data["full_name"]
            delivery_user.phone = delivery_data["phone"]
            delivery_user.password_hash = hash_password(delivery_data["password"])
            delivery_user.role = UserRole.DELIVERY_PARTNER
            delivery_user.is_active = True

    store = db.scalar(select(Store).where(Store.slug == DEFAULT_STORE["slug"]))
    if store is None:
        store = Store(**DEFAULT_STORE)
        db.add(store)
        db.flush()
    else:
        for field, value in DEFAULT_STORE.items():
            setattr(store, field, value)

    categories_by_slug: dict[str, Category] = {}

    for data in CATEGORIES:
        category = db.scalar(select(Category).where(Category.slug == data["slug"]))
        if category is None:
            category = Category(**data)
            db.add(category)
            db.flush()
        else:
            for field, value in data.items():
                setattr(category, field, value)
            category.is_active = True
        categories_by_slug[category.slug] = category

    active_product_slugs = {product["slug"] for product in PRODUCTS}

    for data in PRODUCTS:
        product = db.scalar(select(Product).where(Product.slug == data["slug"]))
        product_data = data.copy()
        category_slug = product_data.pop("category_slug")
        stock_quantity = product_data.pop("stock_quantity")

        if product is None:
            product = Product(category_id=categories_by_slug[category_slug].id)
            db.add(product)

        product.category_id = categories_by_slug[category_slug].id
        for field, value in product_data.items():
            setattr(product, field, value)
        product.is_active = True
        db.flush()

        inventory = db.scalar(
            select(Inventory).where(
                Inventory.store_id == store.id,
                Inventory.product_id == product.id,
            )
        )
        if inventory is None:
            inventory = Inventory(store_id=store.id, product_id=product.id)
            db.add(inventory)
        inventory.stock_quantity = stock_quantity
        inventory.reserved_quantity = min(
            inventory.reserved_quantity or 0,
            stock_quantity,
        )

    for product in db.scalars(select(Product)).all():
        if product.slug not in active_product_slugs:
            product.is_active = False

    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed_catalog(db)
    print("Catalog seed complete.")


if __name__ == "__main__":
    main()

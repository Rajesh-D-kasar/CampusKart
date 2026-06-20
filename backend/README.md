# CampusKart Backend

FastAPI backend for the CampusKart quick-commerce app. It handles catalog,
offers, coupon previews, authentication, cart sync, addresses, checkout, mock
payments, ETA tracking, orders, inventory reservation, and admin catalog/store
operations.

## Stack

- FastAPI
- SQLAlchemy 2
- Alembic
- Pydantic Settings
- JWT authentication
- Argon2 password hashing
- SQLite for local one-click development
- PostgreSQL support through Docker Compose

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

For default SQLite local development:

```powershell
$env:DATABASE_URL = "sqlite:///./dev.db"
python -m alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

For PostgreSQL development:

```powershell
Copy-Item .env.example .env
cd ..
docker compose up -d database
cd backend
python -m alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

Default PostgreSQL connection string:

```text
postgresql+psycopg://campuskart:campuskart@localhost:5432/campuskart
```

## Schema

Alembic creates the commerce schema:

- `users`
- `addresses`
- `stores`
- `categories`
- `products`
- `inventory`
- `carts`
- `cart_items`
- `orders`
- `order_items`

## Seed Data

Run:

```powershell
python -m app.seed
```

The seed command is idempotent. It updates the active development catalog with
27 grocery products. Product names and image URLs are adapted from
[DummyJSON Products](https://dummyjson.com/docs/products); INR prices, stock,
units, categories, and descriptions are synthetic test data.

It also creates a local development admin account:

```text
Email: admin@campuskart.com
Password: AdminPass123
```

## API

| Area | Endpoints |
| --- | --- |
| Health | `GET /health`, `GET /health/database` |
| Products | `GET /products`, `GET /products/categories`, `GET /products/{id}` |
| Offers | `GET /offers`, `POST /offers/coupons/preview` |
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Cart | `GET /cart`, `POST /cart/items`, `PATCH /cart/items/{product_id}`, `DELETE /cart/items/{product_id}`, `DELETE /cart` |
| Addresses | `GET /addresses`, `POST /addresses`, `PATCH /addresses/{id}`, `DELETE /addresses/{id}` |
| Orders | `POST /orders`, `GET /orders`, `GET /orders/{id}` |
| Admin | `GET /admin/summary`, `GET /admin/orders`, `PATCH /admin/orders/{id}/status`, `GET/POST/PATCH /admin/categories`, `GET/POST/PATCH /admin/products`, `GET /admin/inventory`, `PATCH /admin/inventory/{product_id}` |

Interactive docs:

```text
http://127.0.0.1:8000/docs
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests use an isolated SQLite database and do not alter local development data.

Current expected result:

```text
34 passed
```

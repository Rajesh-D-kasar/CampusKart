# CampusKart Backend

FastAPI backend for the CampusKart quick-commerce app. It handles catalog,
offers, coupon previews, authentication, cart sync, addresses, checkout, mock
payments, Razorpay checkout/webhooks, ETA tracking, notifications, invoices,
orders, inventory reservation, delivery operations, and admin catalog/store
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
- Razorpay order, signature verification, webhook, and payment history hooks
- Customer OTP login with expiry, cooldown, attempt limits, and SMTP-ready delivery
- Trusted host middleware and security response headers

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
- `payment_transactions`
- `notifications`
- `delivery_locations`

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

And three local delivery partner accounts:

```text
delivery1@campuskart.com / DeliveryPass123
delivery2@campuskart.com / DeliveryPass123
delivery3@campuskart.com / DeliveryPass123
```

Delivery partners can use `/delivery` after an order is confirmed or packing.

## API

| Area | Endpoints |
| --- | --- |
| Health | `GET /health`, `GET /health/database` |
| Products | `GET /products`, `GET /products/categories`, `GET /products/{id}` |
| Offers | `GET /offers`, `POST /offers/coupons/preview` |
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| OTP Auth | `POST /auth/otp/request`, `POST /auth/otp/verify` |
| Cart | `GET /cart`, `POST /cart/items`, `PATCH /cart/items/{product_id}`, `DELETE /cart/items/{product_id}`, `DELETE /cart` |
| Addresses | `GET /addresses`, `POST /addresses`, `PATCH /addresses/{id}`, `DELETE /addresses/{id}` |
| Orders | `POST /orders`, `GET /orders`, `GET /orders/{id}`, `PATCH /orders/{id}/cancel`, `GET /orders/{id}/invoice` |
| Delivery | `GET /delivery/orders`, `POST /delivery/orders/{id}/location`, `PATCH /delivery/orders/{id}/status` |
| Notifications | `GET /notifications`, `PATCH /notifications/{id}/read` |
| Payments | `POST /payments/razorpay/orders`, `POST /payments/razorpay/verify`, `POST /payments/razorpay/webhook` |
| Admin | `GET /admin/summary`, `GET /admin/analytics`, `GET /admin/orders`, `PATCH /admin/orders/{id}/status`, `PATCH /admin/orders/{id}/items/{item_id}`, `GET/POST/PATCH /admin/categories`, `GET/POST/PATCH /admin/products`, `GET /admin/inventory`, `PATCH /admin/inventory/{product_id}` |

Interactive docs:

```text
http://127.0.0.1:8000/docs
```

## Environment

Important settings:

```text
DATABASE_URL=sqlite:///./dev.db
JWT_SECRET_KEY=replace-this-secret
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
ALLOWED_HOSTS=["localhost","127.0.0.1","testserver"]
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
OTP_EXPIRE_MINUTES=5
OTP_RESEND_COOLDOWN_SECONDS=45
OTP_MAX_ATTEMPTS=5
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
OTP_EMAIL_FROM=no-reply@campuskart.local
```

`postgres://` and `postgresql://` URLs are normalized to the psycopg SQLAlchemy
driver form automatically for common hosting providers.

In development, OTP responses include `development_otp` so the flow can be
tested without email. In production, configure SMTP; otherwise OTP requests
return a clear service-unavailable error instead of pretending to send a code.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests use an isolated SQLite database and do not alter local development data.

Current expected result:

```text
50 passed
```

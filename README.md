# CampusKart

CampusKart is a Blinkit-inspired quick-commerce web app built with React,
FastAPI, SQLAlchemy, and Alembic. It supports browsing a seeded grocery catalog,
authentication, server-side cart sync, delivery addresses, checkout, coupons,
mock payments, ETA-based delivery tracking, and admin catalog/fulfillment
controls.

The project is designed as a practical full-stack learning app: simple enough to
run locally, but structured like a real commerce system.

## Highlights

- Responsive React app with category browsing, product search, cart, checkout,
  and order pages
- Promo banners, coupons, deal collections, and quick product filters
- FastAPI backend with typed Pydantic schemas
- SQLAlchemy 2 models for users, addresses, stores, products, inventory, carts,
  orders, and order items
- Alembic migrations for database schema management
- JWT authentication with password hashing
- Guest cart in browser storage and authenticated cart sync after login
- Address CRUD for checkout
- Cash-on-delivery plus mock UPI/card payment flows
- Store-level inventory and stock reservation during checkout
- My Orders page with ETA, delivery partner, and timeline tracking
- Admin dashboard for order status, category management, product editing, and
  inventory controls
- One-click Windows run script for local development
- Backend and frontend test coverage

## Tech Stack

| Layer | Tools |
| --- | --- |
| Frontend | React 19, Vite, React Router, Axios |
| Backend | FastAPI, SQLAlchemy 2, Pydantic, Uvicorn |
| Database | SQLite for one-click local run, PostgreSQL-ready via Docker Compose |
| Migrations | Alembic |
| Auth | JWT, Argon2 password hashing |
| Tests | Pytest, Node test runner |

## One-Click Run

On Windows, double-click:

```text
run-dev.bat
```

It will:

- prepare the backend virtual environment if needed
- apply database migrations
- seed the development catalog
- install frontend dependencies if needed
- start backend and frontend servers
- open the app at `http://127.0.0.1:5173`

Useful local URLs:

- App: `http://127.0.0.1:5173`
- Backend API: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`
- Database health: `http://127.0.0.1:8000/health/database`

## Manual Setup

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

The one-click flow uses SQLite by default. For PostgreSQL development, copy
`backend/.env.example` to `backend/.env`, start Docker, then run:

```powershell
docker compose up -d database
```

See [backend/README.md](backend/README.md) for backend-specific details.

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Core User Flow

1. Browse grocery products.
2. Search or filter by category.
3. Add products to cart.
4. Register or login.
5. Cart syncs to the backend account.
6. Add or select a delivery address.
7. Apply a coupon, then choose COD, mock UPI, or mock card payment.
8. View the order confirmation, ETA, delivery partner, and tracking timeline.
9. Revisit all placed orders from the Orders page.

## API Overview

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

## Development Admin

The seed command creates a local development admin account:

```text
Email: admin@campuskart.com
Password: AdminPass123
```

Use it to open `/admin`, review store metrics, update order statuses, manage
categories/products, and tune inventory stock/reorder levels. These credentials
are for local development only.

## Test Data

The development catalog uses grocery sample product names and image URLs adapted
from [DummyJSON Products](https://dummyjson.com/docs/products), a public fake API
for testing and prototyping e-commerce applications. INR prices, units, stock,
categories, and descriptions are synthetic data for this learning project.

The active seeded catalog currently includes 27 grocery products across fruits,
vegetables, dairy, beverages, pantry, meat and seafood, frozen desserts, pet
care, household, and nutrition categories.

## Verify

Run backend tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Run frontend tests and build:

```powershell
cd frontend
npm test
npm run build
```

Expected current result:

```text
Backend tests: 34 passed
Frontend tests: 4 passed
Frontend build: passed
```

## Project Structure

```text
blinkit_clone/
|-- backend/
|   |-- app/
|   |   |-- routes/
|   |   |-- auth.py
|   |   |-- config.py
|   |   |-- database.py
|   |   |-- models.py
|   |   |-- schemas.py
|   |   `-- seed.py
|   |-- alembic/
|   `-- tests/
|-- frontend/
|   `-- src/
|       |-- api/
|       |-- components/
|       |-- context/
|       `-- pages/
|-- compose.yaml
|-- run-dev.bat
`-- run-dev.ps1
```

## Roadmap

- Real payment gateway integration
- Dedicated delivery partner dashboard
- Better product detail pages
- Deployment setup

## Notes

This is a learning project and not affiliated with Blinkit, DummyJSON, or any
real quick-commerce brand. The app uses public demo data and synthetic business
data for development/testing only.

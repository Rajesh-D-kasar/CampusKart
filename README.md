# CampusKart

CampusKart is a Blinkit-inspired quick-commerce platform built with React,
FastAPI, SQLAlchemy, and Alembic. It is designed as a realistic learning project
for grocery ordering, store operations, delivery handoff, payments, support, and
admin workflows.

This repository contains four connected surfaces:

- Customer web app for browsing, cart, checkout, orders, wallet, support, and
  tracking.
- Delivery partner website for assigned deliveries, pickup OTP, route updates,
  doorstep OTP, earnings, and support.
- Shop owner website for order packing, rider assignment, pickup OTP, inventory,
  product management, refunds, settlements, and support.
- FastAPI backend that powers authentication, catalog, cart, orders, payments,
  notifications, support, delivery operations, wallet credits, and admin APIs.

> This is a learning project. It is not affiliated with Blinkit, DummyJSON, or
> any real quick-commerce brand.

## Table Of Contents

- [Why This Project Stands Out](#why-this-project-stands-out)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Local URLs](#local-urls)
- [One-Click Run](#one-click-run)
- [Manual Setup](#manual-setup)
- [Common Run Issues](#common-run-issues)
- [Core User Flow](#core-user-flow)
- [Feature Matrix](#feature-matrix)
- [Architecture](#architecture)
- [API Overview](#api-overview)
- [Development Accounts](#development-accounts)
- [Payments And Wallet](#payments-and-wallet)
- [OTP Security](#otp-security)
- [Test Data](#test-data)
- [Verification](#verification)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)

## Why This Project Stands Out

- Full quick-commerce flow from product discovery to OTP-verified delivery.
- Separate customer, delivery partner, and shop owner experiences connected to
  one backend.
- Practical local-store workflow: packing list, rider assignment, pickup OTP,
  substitutions, unavailable-item marking, refunds, and stock management.
- Customer safety flow with two different OTPs: one for store-to-rider pickup
  and one for rider-to-customer delivery.
- Payment stack with COD, mock UPI/card, Razorpay order creation, checkout
  verification, webhook reconciliation, refunds, payment history, settlements,
  and wallet refund credits.
- Support desk for customer, seller, and delivery partner issues with reply
  threads.
- Production-minded foundations: migrations, Dockerfiles, security headers,
  trusted-host validation, deployment config, and tests.

## Tech Stack

| Layer | Tools |
| --- | --- |
| Customer frontend | React 19, Vite, React Router, Axios |
| Delivery panel | React 19, Vite, Axios |
| Shop owner panel | React 19, Vite, Axios |
| Backend | FastAPI, SQLAlchemy 2, Pydantic, Uvicorn |
| Database | SQLite for local run, PostgreSQL-ready through Docker Compose |
| Migrations | Alembic |
| Auth | JWT, Argon2 password hashing |
| OTP | Hashed email OTP, SMTP-ready delivery, dev-mode test code |
| Payments | Razorpay-ready APIs plus local mock payments |
| Tests | Pytest, Node test runner, Vite build |
| Deployment | Docker, Nginx static frontend, Render/Vercel-ready config |

For production setup, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Prerequisites

Install these before running the project locally:

- Windows 10/11 with PowerShell
- Python 3.12
- Node.js 20 or newer
- Git
- Docker Desktop, only if you want PostgreSQL or Docker Compose

Check versions:

```powershell
python --version
node --version
npm --version
git --version
```

## Local URLs

| Surface | URL |
| --- | --- |
| Customer app | `http://127.0.0.1:5173` |
| Delivery partner panel | `http://127.0.0.1:5174` |
| Shop owner panel | `http://127.0.0.1:5175` |
| Backend API | `http://127.0.0.1:8000` |
| API docs | `http://127.0.0.1:8000/docs` |
| Database health | `http://127.0.0.1:8000/health/database` |

## One-Click Run

This is the recommended way to run the full project locally.

1. Open PowerShell.
2. Go to the project folder:

```powershell
cd C:\Users\ASUS\Documents\Codex\blinkit_clone
```

3. Start everything:

```powershell
.\run-dev.ps1
```

If PowerShell blocks the script, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\run-dev.ps1
```

You can also double-click:

```text
run-dev.bat
```

The script will:

- create or reuse the backend virtual environment
- install backend dependencies when needed
- apply Alembic migrations
- seed the development catalog and demo accounts
- install frontend dependencies when needed
- start backend, customer app, delivery panel, and shop owner panel
- open the customer app in the browser

First run may take a few minutes because dependencies are installed. After the
servers start, open:

```text
Customer app:         http://127.0.0.1:5173
Delivery panel:       http://127.0.0.1:5174
Shop owner panel:     http://127.0.0.1:5175
Backend API docs:     http://127.0.0.1:8000/docs
```

To stop the app, press `Ctrl+C` in the running terminals or close the terminal
windows. To start again, run `.\run-dev.ps1` from the project folder.

## Manual Setup

Use this method if you want to run each service in a separate terminal.

### Backend

Open Terminal 1:

```powershell
cd C:\Users\ASUS\Documents\Codex\blinkit_clone
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.seed
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The default local setup uses SQLite. For PostgreSQL development, copy
`backend/.env.example` to `backend/.env`, start Docker, then run:

```powershell
docker compose up -d database
```

### Customer Frontend

Open Terminal 2:

```powershell
cd C:\Users\ASUS\Documents\Codex\blinkit_clone
cd frontend
npm.cmd install
npm.cmd run dev
```

### Delivery Partner Panel

Open Terminal 3:

```powershell
cd C:\Users\ASUS\Documents\Codex\blinkit_clone
cd delivery-panel
npm.cmd install
npm.cmd run dev -- --port 5174
```

### Shop Owner Panel

Open Terminal 4:

```powershell
cd C:\Users\ASUS\Documents\Codex\blinkit_clone
cd shop-owner-panel
npm.cmd install
npm.cmd run dev -- --port 5175
```

### Docker Compose

```powershell
docker compose up --build
```

Then open the URLs listed in [Local URLs](#local-urls).

## Common Run Issues

### `npm.ps1 cannot be loaded`

PowerShell may block `npm` scripts. Use `npm.cmd` instead:

```powershell
npm.cmd install
npm.cmd run dev
```

### `run-dev.ps1 cannot be loaded`

Run the script with a temporary execution-policy bypass:

```powershell
powershell -ExecutionPolicy Bypass -File .\run-dev.ps1
```

### Port already in use

Default ports are:

```text
Backend:          8000
Customer app:     5173
Delivery panel:   5174
Shop owner panel: 5175
```

Close the old terminal running the app, then run `.\run-dev.ps1` again.

### Fresh local database

For a clean local dev database, stop the backend, remove `backend/dev.db`, then
run:

```powershell
cd C:\Users\ASUS\Documents\Codex\blinkit_clone\backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.seed
```

## Core User Flow

1. Customer browses grocery categories, search suggestions, offers, and product
   detail pages.
2. Customer adds items to cart as a guest or logged-in user.
3. Customer registers, logs in with password, or uses customer OTP login.
4. Cart syncs to the backend account after authentication.
5. Customer adds/selects a delivery address and applies a coupon.
6. Customer pays with COD, mock UPI/card, or Razorpay checkout.
7. Shop owner sees the order queue and packing list.
8. Shop owner packs items, handles substitutions/unavailable items, assigns a
   delivery partner, and marks the order ready.
9. Delivery partner enters shop pickup OTP before starting the route.
10. Customer tracks the order and sees the customer delivery OTP.
11. Delivery partner enters the customer OTP before marking delivered.
12. Customer can review the delivered order or open a support ticket.

## Feature Matrix

| Area | Current Capability |
| --- | --- |
| Catalog | Seeded grocery products, categories, images, units, stock, related products |
| Discovery | Search, autocomplete suggestions, quick filters, coupons, promo sections |
| Cart | Guest cart, authenticated cart sync, quantity updates, clear cart |
| Checkout | Address CRUD, coupon preview, COD, mock UPI/card, Razorpay option |
| Orders | ETA, invoice, notifications, cancellation, lifecycle timeline, reviews |
| Wallet | Refund-credit balance and latest transaction history |
| Delivery | Assignment, pickup OTP, location updates, doorstep OTP, earnings |
| Shop owner | Packing list, rider assignment, ready-for-pickup, product and stock tools |
| Payments | Razorpay orders, verification, webhooks, refunds, transaction history |
| Support | Customer, delivery partner, and seller support tickets with replies |
| Admin | Summary, analytics, settlements, orders, categories, products, inventory |
| Security | JWT auth, hashed OTPs, security headers, trusted-host validation |

## Architecture

```text
Customer App (5173)        Delivery Panel (5174)       Shop Owner Panel (5175)
        |                          |                           |
        +--------------------------+---------------------------+
                                   |
                            FastAPI Backend (8000)
                                   |
          +------------------------+------------------------+
          |                        |                        |
   SQLAlchemy Models        Alembic Migrations       External Integrations
          |                                                 |
 SQLite / PostgreSQL                              SMTP, Razorpay, Maps links
```

The three React apps share the same backend API but remain separate so each user
type gets a focused interface.

## API Overview

| Area | Endpoints |
| --- | --- |
| Health | `GET /health`, `GET /health/database` |
| Products | `GET /products`, `GET /products/categories`, `GET /products/suggestions`, `GET /products/{id}`, `GET /products/{id}/recommendations` |
| Offers | `GET /offers`, `POST /offers/coupons/preview` |
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| OTP Auth | `POST /auth/otp/request`, `POST /auth/otp/verify` |
| Cart | `GET /cart`, `POST /cart/items`, `PATCH /cart/items/{product_id}`, `DELETE /cart/items/{product_id}`, `DELETE /cart` |
| Addresses | `GET /addresses`, `POST /addresses`, `PATCH /addresses/{id}`, `DELETE /addresses/{id}` |
| Orders | `POST /orders`, `GET /orders`, `GET /orders/{id}`, `PUT /orders/{id}/review`, `PATCH /orders/{id}/cancel`, `GET /orders/{id}/invoice` |
| Delivery | `GET /delivery/summary`, `GET /delivery/earnings`, `GET /delivery/orders`, `POST /delivery/orders/{id}/location`, `PATCH /delivery/orders/{id}/status` |
| Notifications | `GET /notifications`, `PATCH /notifications/{id}/read` |
| Support | `POST /support/tickets`, `GET /support/tickets`, `POST /support/tickets/{id}/messages`, `GET/PATCH /admin/support/tickets` |
| Payments | `GET /payments/transactions`, `POST /payments/razorpay/orders`, `POST /payments/razorpay/verify`, `POST /payments/razorpay/refunds`, `GET /payments/razorpay/refunds/{refund_id}`, `POST /payments/razorpay/webhook` |
| Wallet | `GET /wallet` |
| Admin | `GET /admin/summary`, `GET /admin/analytics`, `GET /admin/settlements`, `GET /admin/orders`, `PATCH /admin/orders/{id}/status`, `PATCH /admin/orders/{id}/assignment`, `PATCH /admin/orders/{id}/ready`, `PATCH /admin/orders/{id}/items/{item_id}`, `GET /admin/delivery-partners`, `GET/POST/PATCH /admin/categories`, `GET/POST/PATCH /admin/products`, `POST /admin/products/bulk`, `GET /admin/inventory`, `PATCH /admin/inventory/{product_id}` |

## Development Accounts

The seed command creates local demo accounts.

Admin and shop owner access:

```text
Email: admin@campuskart.com
Password: AdminPass123
```

Delivery partner accounts:

```text
Email: delivery1@campuskart.com
Password: DeliveryPass123

Email: delivery2@campuskart.com
Password: DeliveryPass123

Email: delivery3@campuskart.com
Password: DeliveryPass123
```

These credentials are for local development only.

## Payments And Wallet

Local checkout supports COD, mock UPI/card, and Razorpay-ready checkout.

- `POST /payments/razorpay/orders` creates a Razorpay order when credentials are
  configured.
- `POST /payments/razorpay/verify` validates Razorpay payment signatures using
  HMAC SHA-256.
- `POST /payments/razorpay/webhook` validates webhook signatures, records
  payment events, and updates matched order payment status.
- `POST /payments/razorpay/refunds` lets admins execute Razorpay refunds and
  record refund transactions.
- `GET /payments/transactions` returns recent payment/refund transactions for
  reporting.
- Paid order cancellations and successful Razorpay refunds are recorded as
  customer wallet credits at `/wallet`.

Configure Razorpay in `backend/.env` before using real gateway calls:

```text
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
```

## OTP Security

### Customer Login OTP

- OTPs are stored as hashes, not plain text.
- OTPs expire after `OTP_EXPIRE_MINUTES`.
- Resend is limited by `OTP_RESEND_COOLDOWN_SECONDS`.
- Incorrect attempts are limited by `OTP_MAX_ATTEMPTS`.
- OTP login is customer-only; shop owner and delivery accounts use password
  login.
- In development, the OTP is returned on the login page for testing.
- In production, SMTP must be configured.

SMTP example:

```text
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
OTP_EMAIL_FROM=no-reply@example.com
```

### Order Handoff OTP

Delivery security uses two separate OTPs:

1. Shop owner sees a pickup OTP after confirming/packing an order.
2. Delivery partner enters that pickup OTP before moving to `out_for_delivery`.
3. Customer sees a different delivery OTP on the order page.
4. Delivery partner enters the customer OTP before marking the order delivered.

This helps prevent the packed bag from going to the wrong rider and prevents
fake delivery completion without customer confirmation.

## Test Data

The development catalog uses grocery sample product names and image URLs adapted
from [DummyJSON Products](https://dummyjson.com/docs/products), a public fake API
for testing and prototyping e-commerce applications.

INR prices, units, stock, categories, and descriptions are synthetic data for
this learning project. The active seeded catalog includes 27 grocery products
across fruits, vegetables, dairy, beverages, pantry, meat and seafood, frozen
desserts, pet care, household, and nutrition categories.

## Verification

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
Backend tests: 58 passed
Frontend tests: 4 passed
Frontend build: passed
Delivery panel build: passed
Shop owner panel build: passed
```

## Project Structure

```text
blinkit_clone/
|-- backend/
|   |-- Dockerfile
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
|   |-- Dockerfile
|   |-- nginx.conf
|   `-- src/
|       |-- api/
|       |-- components/
|       |-- context/
|       `-- pages/
|-- delivery-panel/
|   |-- Dockerfile
|   |-- index.html
|   |-- nginx.conf
|   `-- src/
|-- shop-owner-panel/
|   |-- Dockerfile
|   |-- index.html
|   |-- nginx.conf
|   `-- src/
|-- deploy/
|   `-- render.yaml
|-- compose.yaml
|-- run-dev.bat
`-- run-dev.ps1
```

## Roadmap

- CI workflow for backend tests, frontend tests, and production builds.
- Production observability dashboard for errors, slow APIs, payment failures,
  refund health, and delivery exceptions.
- Mobile app foundation with Expo/React Native using the same backend APIs.
- Push notifications for order status, pickup, delivery, support replies, and
  wallet credits.
- Real maps/routing integration for delivery partners.
- Seller onboarding, store-level permissions, and multi-store support.

## License And Credits

CampusKart is a private learning project. Product names/images are adapted from
public demo data, and all business logic is synthetic for development/testing.

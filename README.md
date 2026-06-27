# CampusKart

CampusKart is a Blinkit-style full-stack grocery delivery project. It includes a customer shopping app, a shop owner panel, a delivery boy panel, an operations dashboard, and a FastAPI backend API.

The project is built as a practical quick-commerce system for college project review, portfolio presentation, and full-stack learning. It covers product browsing, cart management, checkout, order tracking, OTP-based delivery handoff, inventory management, support tickets, refunds, and delivery operations.

## Project Overview

CampusKart is split into multiple apps that connect to the same backend:

| Module | Purpose |
| --- | --- |
| Customer app | Browse grocery products, manage cart, checkout, track orders, view wallet, and raise support tickets |
| Shop owner panel | Manage orders, packing, rider assignment, inventory, products, refunds, settlements, and support |
| Delivery boy panel | View assigned deliveries, verify OTPs, share location, update delivery status, track earnings, and manage support |
| Admin / operations dashboard | Manage orders, categories, products, inventory, analytics, settlements, and support from `/admin` |
| Backend API | FastAPI service for auth, products, cart, orders, payments, wallet, delivery, support, and admin operations |

The project uses separate frontend folders for customer, delivery, and shop owner views. This keeps each user experience focused while still sharing one API and database.

## Main Modules

### Customer App

Folder: `frontend/`

Main routes:

- `/` home page with banners, categories, offers, and product collections
- `/products` product listing with search, filters, sorting, and suggestions
- `/products/:productId` product detail page with related recommendations
- `/cart` cart page
- `/checkout` address, coupon, and payment flow
- `/orders` customer order history
- `/orders/:orderId` order details, tracking, invoice, cancellation, delivery OTP, and review
- `/wallet` refund credit balance and wallet transaction history
- `/support` support ticket flow
- `/login` and `/register` authentication pages

### Shop Owner Panel

Folder: `shop-owner-panel/`

Implemented features:

- Shop owner/admin login
- Order queue with filters
- Packing list for every order
- Item fulfillment actions: packed, substituted, unavailable
- Delivery partner assignment and reassignment
- Mark order packed/ready for pickup
- Pickup OTP display after order is ready
- Product creation and editing
- Category creation
- Bulk product import from CSV-style text
- Inventory and reorder level controls
- Low-stock list
- Razorpay refund action and refund status check
- Settlement summary
- Seller support tickets and replies

### Delivery Boy Panel

Folder: `delivery-panel/`

Implemented features:

- Delivery partner/admin login
- Assigned order list
- Shift summary and earnings view
- Active, pickup, on-road, and delivered filters
- Search by order, customer, phone, city, or address
- Customer call link
- Map link for delivery address
- Item checklist
- COD collection reminder
- Shop pickup OTP verification before starting route
- Customer delivery OTP verification before completing delivery
- Live location sharing through browser geolocation
- Delivery partner support tickets and replies

### Admin / Operations Dashboard

Route: `/admin`

Implemented features:

- Admin-only access
- Dashboard summary cards
- Recent order management
- Order status update
- Category create/update
- Product create/update
- Inventory quantity, reorder level, and active status update
- Analytics view backed by `/admin/analytics`
- Settlement data backed by `/admin/settlements`

### Backend API

Folder: `backend/`

The backend is a FastAPI app with SQLAlchemy models and Alembic migrations. It includes:

- JWT authentication
- Customer email OTP login
- Product catalog APIs
- Cart APIs
- Address APIs
- Order placement and cancellation
- Order invoice
- Order review
- Store inventory reservation
- Delivery assignment and delivery status updates
- Shop pickup OTP and customer delivery OTP verification
- Notification APIs
- Support ticket APIs
- Razorpay order, verification, webhook, refund, and refund status APIs
- Wallet refund credit APIs
- Admin APIs for orders, delivery partners, categories, products, bulk import, inventory, analytics, and settlements

## Features

### Customer Features

- Browse grocery catalog by category
- Search and product suggestions
- Product detail pages
- Related product recommendations
- Guest cart and authenticated cart sync
- Address CRUD
- Coupon preview and discount application
- Cash on delivery
- Demo UPI/card payment flow
- Razorpay checkout integration when keys are configured
- Order confirmation and tracking timeline
- Invoice view
- Order cancellation
- Delivery OTP display
- Delivered order review and ratings
- Wallet refund credit history
- Support ticket creation and replies

### Shop Owner Features

- View and filter store orders
- See packing list and item quantities
- Mark items packed, substituted, or unavailable
- Assign delivery partner
- Mark order ready for pickup
- Show pickup OTP for safe handoff
- Manage stock quantity and reorder level
- Add and update products
- Add categories
- Bulk product import
- Trigger Razorpay refund for paid Razorpay orders
- Check refund status
- View settlement cards
- Manage support tickets

### Delivery Boy Features

- View assigned deliveries
- See delivery summary and estimated earnings
- Start route only after shop pickup OTP verification
- Complete delivery only after customer OTP verification
- Share live delivery location
- Open map for customer address
- Call customer
- Track COD collection requirement
- Create and reply to support tickets

### Backend Features

- FastAPI app with OpenAPI docs
- SQLAlchemy 2 models
- Alembic migrations
- SQLite default local run
- PostgreSQL support through Docker Compose
- JWT auth with Argon2 password hashing
- Hashed OTP login flow with expiry, cooldown, and max attempts
- Trusted host middleware
- CORS configuration
- Security response headers
- Pytest backend test suite

## Tech Stack

| Layer | Technology |
| --- | --- |
| Customer app | React 19, Vite, React Router, Axios |
| Shop owner panel | React 19, Vite, browser Fetch API |
| Delivery boy panel | React 19, Vite, browser Fetch API |
| Backend | FastAPI, SQLAlchemy 2, Pydantic Settings, Uvicorn |
| Database | SQLite for local development, PostgreSQL through Docker Compose |
| Migrations | Alembic |
| Authentication | JWT, Argon2 password hashing, email OTP flow |
| Payments | Razorpay-ready backend APIs, demo UPI/card flow, COD |
| Testing | Pytest, Node test runner |
| Deployment | Docker, Nginx, Render blueprint, Vercel rewrites |

## Screenshots / Demo

Screenshots are not committed yet.

Suggested folder:

```text
docs/screenshots/
```

Suggested screenshots to add:

- Customer home page
- Product listing page
- Product detail page
- Cart and checkout
- Order tracking page
- Customer wallet page
- Shop owner order queue
- Shop owner inventory screen
- Delivery boy active order screen
- Admin dashboard
- FastAPI Swagger docs at `http://127.0.0.1:8000/docs`

After adding images, reference them here like:

```md
![Customer Home](docs/screenshots/customer-home.png)
```

## Folder Structure

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
|   |-- tests/
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- requirements-dev.txt
|-- frontend/
|   |-- src/
|   |   |-- api/
|   |   |-- components/
|   |   |-- context/
|   |   |-- pages/
|   |   `-- utils/
|   |-- Dockerfile
|   |-- package.json
|   |-- nginx.conf
|   `-- vercel.json
|-- delivery-panel/
|   |-- src/
|   |-- Dockerfile
|   |-- package.json
|   |-- nginx.conf
|   `-- vercel.json
|-- shop-owner-panel/
|   |-- src/
|   |-- Dockerfile
|   |-- package.json
|   |-- nginx.conf
|   `-- vercel.json
|-- deploy/
|   `-- render.yaml
|-- compose.yaml
|-- DEPLOYMENT.md
|-- run-dev.bat
|-- run-dev.ps1
`-- README.md
```

## How To Run Locally

### Prerequisites

Install:

- Python 3.12 or compatible Python version
- Node.js 20 or newer
- Git
- Docker Desktop, only if using Docker Compose / PostgreSQL

Check versions:

```powershell
python --version
node --version
npm --version
git --version
```

### Recommended One-Click Run On Windows

From the project root:

```powershell
.\run-dev.ps1
```

If PowerShell blocks scripts:

```powershell
powershell -ExecutionPolicy Bypass -File .\run-dev.ps1
```

You can also run:

```text
run-dev.bat
```

The script prepares the backend, applies migrations, seeds data, installs frontend dependencies when needed, starts all apps, and opens the browser.

Local URLs:

| App | URL |
| --- | --- |
| Customer app | `http://127.0.0.1:5173` |
| Delivery boy panel | `http://127.0.0.1:5174` |
| Shop owner panel | `http://127.0.0.1:5175` |
| Backend API | `http://127.0.0.1:8000` |
| API docs | `http://127.0.0.1:8000/docs` |
| Database health | `http://127.0.0.1:8000/health/database` |

## Backend Setup

Open a terminal in the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

For local SQLite:

```powershell
$env:DATABASE_URL = "sqlite:///./dev.db"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.seed
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

## Frontend / Customer App Setup

Open another terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Customer app runs at:

```text
http://127.0.0.1:5173
```

Useful commands from `frontend/package.json`:

```powershell
npm.cmd run dev
npm.cmd run build
npm.cmd test
npm.cmd run preview
```

## Shop Owner Panel Setup

The shop owner panel uses Vite from the customer frontend dependencies. Install the customer frontend dependencies first:

```powershell
cd frontend
npm.cmd install
```

Then run:

```powershell
cd ..\shop-owner-panel
npm.cmd run dev
```

Shop owner panel runs at:

```text
http://127.0.0.1:5175
```

Useful commands from `shop-owner-panel/package.json`:

```powershell
npm.cmd run dev
npm.cmd run build
npm.cmd run preview
```

## Delivery Panel Setup

The delivery panel also uses Vite from the customer frontend dependencies.

```powershell
cd frontend
npm.cmd install
cd ..\delivery-panel
npm.cmd run dev
```

Delivery panel runs at:

```text
http://127.0.0.1:5174
```

Useful commands from `delivery-panel/package.json`:

```powershell
npm.cmd run dev
npm.cmd run build
npm.cmd run preview
```

## Admin Panel Setup

The admin dashboard is part of the customer React app.

Run the backend and customer frontend, then open:

```text
http://127.0.0.1:5173/admin
```

Demo admin login:

```text
Email: admin@campuskart.com
Password: AdminPass123
```

## Demo Accounts

The seed command creates these local accounts:

```text
Admin / shop owner:
admin@campuskart.com / AdminPass123

Delivery partners:
delivery1@campuskart.com / DeliveryPass123
delivery2@campuskart.com / DeliveryPass123
delivery3@campuskart.com / DeliveryPass123
```

Customers can register from the app or use OTP login.

## Environment Variables

### Backend

The backend reads environment variables through `backend/app/config.py`. You can create `backend/.env` to override defaults.

Important variables:

```env
APP_NAME=CampusKart API
ENVIRONMENT=development
DATABASE_URL=sqlite:///./dev.db
JWT_SECRET_KEY=change-this-dev-secret-before-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173","http://localhost:5174","http://127.0.0.1:5174","http://localhost:5175","http://127.0.0.1:5175"]
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
SMTP_USE_TLS=true
OTP_EMAIL_FROM=no-reply@campuskart.local
```

### Customer App

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_DELIVERY_PANEL_URL=http://127.0.0.1:5174
VITE_SHOP_OWNER_PANEL_URL=http://127.0.0.1:5175
```

### Delivery Panel

```env
VITE_API_URL=http://127.0.0.1:8000
```

### Shop Owner Panel

```env
VITE_API_URL=http://127.0.0.1:8000
```

## API Overview

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Main API groups:

| Area | Endpoints |
| --- | --- |
| Health | `GET /`, `GET /health`, `GET /health/database` |
| Products | `GET /products`, `GET /products/categories`, `GET /products/suggestions`, `GET /products/{id}`, `GET /products/{id}/recommendations` |
| Offers | `GET /offers`, `POST /offers/coupons/preview` |
| Auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/otp/request`, `POST /auth/otp/verify`, `GET /auth/me` |
| Cart | `GET /cart`, `POST /cart/items`, `PATCH /cart/items/{product_id}`, `DELETE /cart/items/{product_id}`, `DELETE /cart` |
| Addresses | `GET /addresses`, `POST /addresses`, `PATCH /addresses/{id}`, `DELETE /addresses/{id}` |
| Orders | `POST /orders`, `GET /orders`, `GET /orders/{id}`, `PUT /orders/{id}/review`, `PATCH /orders/{id}/cancel`, `GET /orders/{id}/invoice` |
| Delivery | `GET /delivery/summary`, `GET /delivery/earnings`, `GET /delivery/orders`, `POST /delivery/orders/{id}/location`, `PATCH /delivery/orders/{id}/status` |
| Payments | `GET /payments/transactions`, `POST /payments/razorpay/orders`, `POST /payments/razorpay/verify`, `POST /payments/razorpay/refunds`, `GET /payments/razorpay/refunds/{refund_id}`, `POST /payments/razorpay/webhook` |
| Wallet | `GET /wallet` |
| Notifications | `GET /notifications`, `PATCH /notifications/{id}/read` |
| Support | `POST /support/tickets`, `GET /support/tickets`, `POST /support/tickets/{id}/messages`, `GET /admin/support/tickets`, `PATCH /admin/support/tickets/{id}` |
| Admin | `GET /admin/summary`, `GET /admin/analytics`, `GET /admin/settlements`, `GET /admin/orders`, `GET /admin/delivery-partners`, `PATCH /admin/orders/{id}/status`, `PATCH /admin/orders/{id}/assignment`, `PATCH /admin/orders/{id}/ready`, `PATCH /admin/orders/{id}/items/{item_id}`, `GET/POST/PATCH /admin/categories`, `GET/POST/PATCH /admin/products`, `POST /admin/products/bulk`, `GET /admin/inventory`, `PATCH /admin/inventory/{product_id}` |

## Docker And Deployment

### Docker Compose

The repository includes `compose.yaml` with services for:

- PostgreSQL database
- FastAPI backend
- Customer frontend
- Delivery panel
- Shop owner panel

Run:

```powershell
docker compose up --build
```

Then open:

```text
Customer app:      http://127.0.0.1:5173
Delivery panel:    http://127.0.0.1:5174
Shop owner panel:  http://127.0.0.1:5175
Backend API:       http://127.0.0.1:8000
```

### Backend Dockerfile

The backend Dockerfile installs `backend/requirements.txt`, runs Alembic migrations, seeds baseline data, and starts Uvicorn.

Start command from `backend/Dockerfile`:

```sh
alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Render / Vercel

Deployment files included:

- `deploy/render.yaml` for Render Docker services
- `frontend/vercel.json`
- `delivery-panel/vercel.json`
- `shop-owner-panel/vercel.json`
- Dockerfiles for backend, customer frontend, delivery panel, and shop owner panel

More deployment notes are in:

```text
DEPLOYMENT.md
```

## Testing And Verification

Backend tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Frontend tests:

```powershell
cd frontend
npm.cmd test
```

Build customer app:

```powershell
cd frontend
npm.cmd run build
```

Build delivery panel:

```powershell
cd delivery-panel
npm.cmd run build
```

Build shop owner panel:

```powershell
cd shop-owner-panel
npm.cmd run build
```

The backend test suite currently contains tests for health checks, catalog, search, cart, addresses, auth, OTP login, orders, coupons, delivery, admin, support, migrations, payments, refunds, wallet credits, and reviews.

## Current Project Status

Current status: functional full-stack development version.

Implemented and verified in code:

- Customer web app
- Backend API
- Shop owner panel
- Delivery boy panel
- Admin dashboard
- SQLite local development
- PostgreSQL Docker Compose setup
- Alembic migrations
- Demo seed data
- Backend tests
- Frontend tests and builds
- Dockerfiles and deployment configuration

The project is ready for local demo, GitHub showcase, and college project review. Production use would still require real domain setup, production secrets, SMTP configuration, Razorpay production keys, monitoring, and security review.

## Future Improvements

Planned or possible improvements:

- Add real screenshots and demo video links
- Add CI workflow for backend tests and frontend builds
- Add mobile app using the same backend APIs
- Add production monitoring and error logging
- Add real-time order updates with WebSockets or server-sent events
- Add advanced seller roles and multi-store permissions
- Add better delivery route optimization
- Add push notifications for order and support updates
- Add more payment provider test cases

## What I Learned

While building this project, I practiced:

- Designing a multi-role full-stack application
- Building REST APIs with FastAPI
- Using SQLAlchemy models and relationships
- Managing database migrations with Alembic
- Implementing JWT authentication and OTP login
- Connecting multiple React/Vite apps to one backend
- Handling cart, checkout, order, inventory, and delivery workflows
- Working with Razorpay-style payment and refund flows
- Writing backend and frontend tests
- Preparing Docker and deployment-ready project structure
- Writing project documentation for real reviewers and recruiters

## Author

Rajesh

GitHub: [Rajesh-D-kasar](https://github.com/Rajesh-D-kasar)

## Notes

This project is not affiliated with Blinkit. Product names and images in seed data are adapted from public demo grocery data. Prices, inventory, users, and business data are for development and testing only.
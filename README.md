# CampusKart

CampusKart is a Blinkit-inspired quick-commerce project for browsing campus
essentials, searching the catalog, and managing a persistent shopping cart.

## Current Features

- Responsive React interface with page routing
- Product catalog loaded from FastAPI
- Product search
- Add, remove, and update cart quantities
- Cart persistence in browser storage
- Automatic subtotal and delivery-fee calculation
- FastAPI health and product endpoints
- Frontend cart tests and backend API tests

Authentication, checkout, database persistence, admin tools, and payments are
planned but are not presented as complete yet.

## Run the Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

## Run the Frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Verify

```powershell
cd frontend
npm test
npm run build

cd ..\backend
.\.venv\Scripts\python.exe -m pytest
```

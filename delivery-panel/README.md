# CampusKart Delivery Panel

Separate delivery partner website connected to the CampusKart backend.

## Local Run

Start the main project:

```powershell
.\run-dev.ps1
```

Open:

```text
http://127.0.0.1:5174
```

Demo logins:

```text
delivery1@campuskart.com / DeliveryPass123
delivery2@campuskart.com / DeliveryPass123
delivery3@campuskart.com / DeliveryPass123
```

## Features

- Delivery partner/admin login
- Assigned order list from `/delivery/orders`
- Shift summary from `/delivery/summary`
- Active, pickup, on-road, and delivered tabs
- Search by order, customer, phone, city, or address
- Call customer and open map actions
- Item checklist per order
- COD collection reminder
- Status updates for out-for-delivery and delivered

## Environment

```text
VITE_API_URL=http://127.0.0.1:8000
```

For deployment, set `VITE_API_URL` to the deployed backend URL and make sure the
backend `CORS_ORIGINS` allows this delivery panel domain.

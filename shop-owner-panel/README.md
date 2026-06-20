# CampusKart Shop Owner Panel

Separate shop owner website connected to the CampusKart backend.

## Local Run

Start everything:

```powershell
.\run-dev.ps1
```

Open:

```text
http://127.0.0.1:5175
```

Demo owner login:

```text
admin@campuskart.com / AdminPass123
```

## Features

- Simple shop owner login
- Order queue with quick status buttons
- Open/new/packing/done/all filters
- Stock management with large, simple controls
- Low-stock warning list
- Add product form
- Add category form
- Connected to existing `/admin/*` backend APIs

## Environment

```text
VITE_API_URL=http://127.0.0.1:8000
```

For deployment, set `VITE_API_URL` to the backend URL and add this panel domain
to backend `CORS_ORIGINS`.

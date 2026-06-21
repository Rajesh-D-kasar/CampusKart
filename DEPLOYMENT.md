# CampusKart Deployment Guide

This project is split into four deployable apps:

- FastAPI backend in `backend/`
- Customer web app in `frontend/`
- Delivery partner panel in `delivery-panel/`
- Shop owner panel in `shop-owner-panel/`

## Backend on Render

1. Create a PostgreSQL database on Render.
2. Create a web service from this repository.
3. Use `deploy/render.yaml` as the blueprint, or create the service manually with:
   - Root: repository root
   - Dockerfile: `backend/Dockerfile`
   - Health check: `/health`
4. Add production environment variables:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
JWT_SECRET_KEY=replace-with-a-long-random-secret
CORS_ORIGINS=["https://your-customer-app.vercel.app","https://your-delivery-panel.vercel.app","https://your-shop-panel.vercel.app"]
ALLOWED_HOSTS=["your-api.onrender.com","localhost","127.0.0.1"]
RAZORPAY_KEY_ID=rzp_live_or_test_key
RAZORPAY_KEY_SECRET=rzp_live_or_test_secret
RAZORPAY_WEBHOOK_SECRET=copy-from-razorpay-dashboard-webhook-settings
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
OTP_EMAIL_FROM=no-reply@example.com
```

The backend Docker start command runs Alembic migrations, seeds baseline data,
and starts Uvicorn.

## Web Apps on Vercel

Deploy each folder as a separate Vercel project:

| App | Root directory | Build command | Output |
| --- | --- | --- | --- |
| Customer | `frontend` | `npm run build` | `dist` |
| Delivery panel | `delivery-panel` | `npm run build` | `dist` |
| Shop owner panel | `shop-owner-panel` | `npm run build` | `dist` |

Set this variable in all three web apps:

```env
VITE_API_URL=https://your-api.onrender.com
```

Customer app also supports:

```env
VITE_DELIVERY_PANEL_URL=https://your-delivery-panel.vercel.app
VITE_SHOP_OWNER_PANEL_URL=https://your-shop-panel.vercel.app
```

## Production Checklist

- Run `alembic upgrade head` against production database before public launch.
- Confirm `/health` returns `{"status":"ok"}`.
- Verify customer OTP email delivery in SMTP mode.
- Test one cash-on-delivery order end to end.
- Test one Razorpay test-mode payment end to end.
- Test one Razorpay test-mode refund from the shop owner panel.
- Check the refund status button after the test refund and verify settlement cards update.
- Configure the Razorpay webhook URL:
  `https://your-api.onrender.com/payments/razorpay/webhook`.
- Enable Razorpay `payment.captured`, `payment.failed`, and refund events.
- Confirm shop pickup OTP and customer delivery OTP both work.
- Confirm delivery partner live location sharing works over HTTPS.
- Confirm customer, delivery partner, and seller support tickets can receive replies.
- Add the deployed domains to backend `CORS_ORIGINS` and `ALLOWED_HOSTS`.
- Rotate `JWT_SECRET_KEY` if it was ever shared in screenshots or logs.

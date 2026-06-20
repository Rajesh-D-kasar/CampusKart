from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.routes.admin import router as admin_router
from app.routes.addresses import router as addresses_router
from app.routes.cart import router as cart_router
from app.routes.offers import router as offers_router
from app.routes.orders import router as orders_router
from app.routes.products import router as products_router
from app.routes.users import router as users_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Backend API for the CampusKart quick-commerce app.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(offers_router)
app.include_router(users_router)
app.include_router(cart_router)
app.include_router(addresses_router)
app.include_router(orders_router)
app.include_router(admin_router)


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "CampusKart backend is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/database")
def database_health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}

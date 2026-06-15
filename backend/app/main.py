from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.products import router as products_router

app = FastAPI(
    title="CampusKart API",
    description="Backend API for the CampusKart quick-commerce app.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "CampusKart backend is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CampusKart API"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg://campuskart:campuskart@localhost:5432/campuskart"
    )
    jwt_secret_key: str = "change-this-dev-secret-before-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    razorpay_webhook_secret: str | None = None
    otp_expire_minutes: int = 5
    otp_resend_cooldown_seconds: int = 45
    otp_max_attempts: int = 5
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    otp_email_from: str = "no-reply@campuskart.local"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # -> app/


class Settings(BaseSettings):
    # =========================
    # ✅ DATABASE / AUTH
    # =========================
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # =========================
    # ✅ PAYMENT
    # =========================
    PAYMENT_MODE: str = "MOCK"
    RAZORPAY_KEY_ID: str | None = None
    RAZORPAY_KEY_SECRET: str | None = None

    # =========================
    # ✅ EMAIL SETTINGS (NEW)
    # =========================
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    EMAIL_FROM: str | None = None  # optional

    GOOGLE_MAPS_API_KEY: str | None = None

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"   # 🔥 VERY IMPORTANT


settings = Settings()

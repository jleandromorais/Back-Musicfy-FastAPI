# app/core/config.py

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    FRONTEND_URL: str
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174", "https://musicfy-two.vercel.app"]
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_SERVICE_ACCOUNT_PATH: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
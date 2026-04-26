# app/core/config.py

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:5173"
    # Aceita string separada por vírgula: "https://meusite.vercel.app,http://localhost:5173"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:5174,https://musicfy-two.vercel.app"
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_SERVICE_ACCOUNT_PATH: str = ""
    FIREBASE_SERVICE_ACCOUNT_JSON: str = ""  # JSON completo como string (para produção)

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

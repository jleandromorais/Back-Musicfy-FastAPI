from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    
    
    # Database
    DATABASE_URL: str
    
    #Security
    
    SECRET_KEY: str
    ALGORITHM: str= "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    #Stripe
    
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str  
    
    #CORS
    FRONTTED_URL: str
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "https://musicfy-two.vercel.app"]
     
     
    class  Config:
        env_file= ".env"
        case_sensitive = True
        
settings = Settings()

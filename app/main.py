# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth

# Criar app
app = FastAPI(
    title="Musicfy API",
    description="Backend FastAPI para e-commerce de produtos de áudio",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(auth.router, prefix="/api")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Musicfy API is running"}

# Root
@app.get("/")
async def root():
    return {
        "message": "Welcome to Musicfy API",
        "docs": "/docs",
        "health": "/health"
    }
# app/main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.routes import auth, products, usuario, enderecos, checkout, carrinho, orders
from app.api.routes.admin import auth as admin_auth
from app.api.routes.admin import products as admin_products

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
app.include_router(products.router, prefix="/api")
app.include_router(usuario.router, prefix="/api")
app.include_router(enderecos.router, prefix="/api")
app.include_router(checkout.router, prefix="/api")
app.include_router(carrinho.router, prefix="/api")
app.include_router(orders.router, prefix="/api")

# Rotas admin
app.include_router(admin_auth.router, prefix="/api")
app.include_router(admin_products.router, prefix="/api")

# Servir imagens de upload
os.makedirs("uploads/products", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
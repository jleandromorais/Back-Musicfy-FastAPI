# app/models/product.py

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class CategoryEnum(enum.Enum):
    FONES = "fones"
    HEADSETS = "headsets"
    CAIXAS_SOM = "caixas_som"
    ACESSORIOS = "acessorios"

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, index=True)
    descricao = Column(String)
    preco = Column(Float, nullable=False)
    imagem_url = Column(String)
    categoria = Column(SQLEnum(CategoryEnum), nullable=False)
    estoque = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
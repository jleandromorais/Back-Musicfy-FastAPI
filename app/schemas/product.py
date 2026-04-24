# app/schemas/product.py

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.product import CategoryEnum


#Schema base (Campos comuns)

class ProductBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    descricao: Optional[str] = None
    preco: float = Field(..., gt=0)
    imagem_url: Optional[str] = None
    categoria: CategoryEnum
    estoque: int = Field(0, ge=0)
    
# Schema para criação

class ProductCreate(ProductBase):
    pass

# Schema para resposta (sem campos de relacionamento)
class ProductUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=100)
    descricao: Optional[str] = None
    preco: Optional[float] = Field(None, gt=0)
    imagem_url: Optional[str] = None
    categoria: Optional[CategoryEnum] = None
    estoque: Optional[int] = Field(None, ge=0)
    

#Schema para resposta

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    
#Schema para listagem com paginacao

class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    
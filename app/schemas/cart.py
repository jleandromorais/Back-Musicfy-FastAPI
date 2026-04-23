# app/schemas/cart.py

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.schemas.product import ProductResponse

# Schema do item do carrinho
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)

class CartItemCreate(CartItemBase):
    pass

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    product: ProductResponse  # Incluir dados do produto
    subtotal: float  # Calculado: product.preco * quantity
    
    model_config = ConfigDict(from_attributes=True)

# Schema do carrinho
class CartBase(BaseModel):
    pass

class CartCreate(BaseModel):
    user_id: Optional[int] = None

class CartResponse(BaseModel):
    id: int
    user_id: Optional[int]
    items: List[CartItemResponse]
    total: float  # Soma de todos os subtotals
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)

# Schema para adicionar item
class AddItemRequest(BaseModel):
    productId: int = Field(..., alias="productId")  # Frontend envia assim
    quantity: int = Field(default=1, ge=1)
    
    model_config = ConfigDict(populate_by_name=True)
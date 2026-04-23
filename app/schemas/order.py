# app/schemas/order.py

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional
from app.models.order import OrderStatus
from app.schemas.product import ProductResponse

# Schema do item do pedido
class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_purchase: float
    product: ProductResponse
    subtotal: float  # Calculado: price_at_purchase * quantity
    
    model_config = ConfigDict(from_attributes=True)

# Schema do pedido
class OrderBase(BaseModel):
    shipping_address: str = Field(..., min_length=10)

class OrderCreate(OrderBase):
    cart_id: int

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total: float
    status: OrderStatus
    shipping_address: str
    items: List[OrderItemResponse]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class OrderListResponse(BaseModel):
    items: List[OrderResponse]
    total: int
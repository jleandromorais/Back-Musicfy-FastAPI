# app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional

#Schema base (Campos comumns)

class UserBase(BaseModel):
    email: EmailStr
    nome : str = Field(..., min_length=2, max_length=100)
    
# Schema para criação (registro)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    
# Schema para Uppdate

class UserUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=6)
    
# Schema para resposta (sem senha)

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
#Schema para login 

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    
#Schema para token

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class TokenData(BaseModel):
    email: Optional[str] = None
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.models.user import User

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])


class AdminLoginPayload(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
async def admin_login(payload: AdminLoginPayload, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso negado. Verifique suas credenciais.",
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Verifique suas credenciais.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conta inativa.",
        )

    access_token = create_access_token(
        data={"sub": user.email, "role": "admin"},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": {"id": user.id, "nome": user.nome, "email": user.email},
    }

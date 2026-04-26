from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import timedelta, datetime
from collections import defaultdict
import threading

from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.models.user import User

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])

# Rate limiting em memória — 5 tentativas por IP a cada 15 minutos
_attempts: dict = defaultdict(list)
_lock = threading.Lock()
_MAX_ATTEMPTS = 5
_WINDOW_MINUTES = 15


def _check_rate_limit(ip: str) -> None:
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=_WINDOW_MINUTES)

    with _lock:
        # Remove tentativas fora da janela
        _attempts[ip] = [t for t in _attempts[ip] if t > window_start]

        if len(_attempts[ip]) >= _MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Muitas tentativas. Aguarde {_WINDOW_MINUTES} minutos.",
                headers={"Retry-After": str(_WINDOW_MINUTES * 60)},
            )

        _attempts[ip].append(now)


def _clear_attempts(ip: str) -> None:
    with _lock:
        _attempts.pop(ip, None)


class AdminLoginPayload(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
async def admin_login(
    payload: AdminLoginPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # IP real (considera proxy reverso)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()

    _check_rate_limit(client_ip)

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

    # Login bem-sucedido — limpa tentativas do IP
    _clear_attempts(client_ip)

    access_token = create_access_token(
        data={"sub": user.email, "role": "admin"},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": {"id": user.id, "nome": user.nome, "email": user.email},
    }

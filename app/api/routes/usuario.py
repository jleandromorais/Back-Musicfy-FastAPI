from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.firebase import verify_firebase_token
from app.models.user import User

router = APIRouter(prefix="/usuario", tags=["Usuario"])


class FirebaseUserCreate(BaseModel):
    firebaseUid: str
    fullName: str
    email: str


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "fullName": user.nome,
        "email": user.email,
        "firebaseUid": user.firebase_uid,
    }


def _extract_uid(authorization: Optional[str]) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return verify_firebase_token(authorization[7:])


@router.get("/firebase/{firebase_uid}")
async def get_by_firebase_uid(
    firebase_uid: str,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    uid = _extract_uid(authorization)
    if uid and uid != firebase_uid:
        raise HTTPException(status_code=403, detail="Acesso negado")

    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return _user_to_dict(user)


@router.post("/criar", status_code=201)
async def criar_usuario(
    data: FirebaseUserCreate,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    # Verifica se já existe
    result = await db.execute(select(User).where(User.firebase_uid == data.firebaseUid))
    existing = result.scalar_one_or_none()
    if existing:
        return _user_to_dict(existing)

    # Verifica se email já está em uso por outro usuário
    result = await db.execute(select(User).where(User.email == data.email))
    email_user = result.scalar_one_or_none()
    if email_user:
        # Associa firebase_uid ao usuário existente
        email_user.firebase_uid = data.firebaseUid
        await db.commit()
        await db.refresh(email_user)
        return _user_to_dict(email_user)

    user = User(
        email=data.email,
        nome=data.fullName,
        firebase_uid=data.firebaseUid,
        password_hash=None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _user_to_dict(user)

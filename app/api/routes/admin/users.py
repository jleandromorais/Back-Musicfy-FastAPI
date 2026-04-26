from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_admin

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


def _user_to_dict(u: User) -> dict:
    return {
        "id":          u.id,
        "nome":        u.nome,
        "email":       u.email,
        "firebaseUid": u.firebase_uid,
        "isActive":    u.is_active,
        "isAdmin":     u.is_admin,
        "createdAt":   u.created_at.isoformat() if u.created_at else None,
    }


@router.get("/")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    query = select(User)
    count_query = select(func.count()).select_from(User)

    if search:
        pattern = f"%{search}%"
        query = query.where(User.nome.ilike(pattern) | User.email.ilike(pattern))
        count_query = count_query.where(User.nome.ilike(pattern) | User.email.ilike(pattern))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    offset = (page - 1) * limit
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return {"users": [_user_to_dict(u) for u in users], "total": total, "page": page}


@router.patch("/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_active = not user.is_active
    await db.commit()
    return _user_to_dict(user)

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.address import Address

router = APIRouter(prefix="/enderecos", tags=["Enderecos"])


class AddressCreate(BaseModel):
    cep: str
    rua: str
    numero: str
    complemento: Optional[str] = None
    bairro: str
    cidade: str
    estado: str
    tipo: Optional[str] = "casa"
    userId: Optional[int] = None
    firebaseUid: Optional[str] = None
    metodoEntrega: Optional[str] = None


@router.post("/", status_code=201)
async def criar_endereco(data: AddressCreate, db: AsyncSession = Depends(get_db)):
    address = Address(
        user_id=data.userId,
        cep=data.cep,
        rua=data.rua,
        numero=data.numero,
        complemento=data.complemento,
        bairro=data.bairro,
        cidade=data.cidade,
        estado=data.estado,
        tipo=data.tipo or "casa",
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return {"id": address.id, "message": "Endereço criado com sucesso"}

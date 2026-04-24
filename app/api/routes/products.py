from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.models.product import Product, CategoryEnum
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=list[ProductResponse])
async def list_products(
    categoria: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Product).where(Product.estoque > 0)
    if categoria:
        try:
            cat = CategoryEnum(categoria)
            query = query.where(Product.categoria == cat)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Categoria inválida: {categoria}")
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product

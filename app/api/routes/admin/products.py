import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, case

from app.core.database import get_db
from app.models.product import Product, CategoryEnum
from app.api.dependencies import get_current_admin

router = APIRouter(prefix="/admin/products", tags=["Admin Products"])

UPLOAD_DIR = "uploads/products"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _product_to_dict(p: Product) -> dict:
    return {
        "id": p.id,
        "nome": p.nome,
        "descricao": p.descricao,
        "preco": p.preco,
        "imagem_url": p.imagem_url,
        "categoria": p.categoria.value,
        "estoque": p.estoque,
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


async def _save_image(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return f"/uploads/products/{filename}"


@router.get("/metrics")
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    total_result = await db.execute(select(func.count()).select_from(Product))
    total = total_result.scalar()

    active_result = await db.execute(
        select(func.count()).select_from(Product).where(Product.is_active == True)
    )
    active = active_result.scalar()

    no_stock_result = await db.execute(
        select(func.count()).select_from(Product).where(Product.estoque == 0)
    )
    no_stock = no_stock_result.scalar()

    return {"total": total, "active": active, "out_of_stock": no_stock}


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    # Produtos por categoria com contagem e valor total de estoque
    cat_result = await db.execute(
        select(
            Product.categoria,
            func.count(Product.id).label("quantidade"),
            func.sum(Product.preco * Product.estoque).label("valor_estoque"),
            func.avg(Product.preco).label("preco_medio"),
        ).group_by(Product.categoria)
    )
    by_category = [
        {
            "categoria": row.categoria.value,
            "quantidade": row.quantidade,
            "valor_estoque": round(float(row.valor_estoque or 0), 2),
            "preco_medio": round(float(row.preco_medio or 0), 2),
        }
        for row in cat_result.all()
    ]

    # Distribuição de estoque (sem estoque / baixo / ok)
    stock_result = await db.execute(
        select(
            func.count(case((Product.estoque == 0, 1))).label("sem_estoque"),
            func.count(case((Product.estoque.between(1, 5), 1))).label("estoque_baixo"),
            func.count(case((Product.estoque > 5, 1))).label("estoque_ok"),
        )
    )
    stock_row = stock_result.one()
    stock_distribution = [
        {"name": "Sem estoque", "value": stock_row.sem_estoque, "fill": "#ef4444"},
        {"name": "Estoque baixo (1-5)", "value": stock_row.estoque_baixo, "fill": "#f97316"},
        {"name": "Estoque ok (>5)", "value": stock_row.estoque_ok, "fill": "#22c55e"},
    ]

    # Top 8 produtos com maior estoque
    top_result = await db.execute(
        select(Product.nome, Product.estoque, Product.categoria)
        .where(Product.estoque > 0)
        .order_by(Product.estoque.desc())
        .limit(8)
    )
    top_stock = [
        {"nome": row.nome[:20] + ("…" if len(row.nome) > 20 else ""), "estoque": row.estoque}
        for row in top_result.all()
    ]

    # Status ativo vs inativo
    status_result = await db.execute(
        select(
            func.count(case((Product.is_active == True, 1))).label("ativos"),
            func.count(case((Product.is_active == False, 1))).label("inativos"),
        )
    )
    status_row = status_result.one()
    status_distribution = [
        {"name": "Ativos", "value": status_row.ativos, "fill": "#f97316"},
        {"name": "Inativos", "value": status_row.inativos, "fill": "#374151"},
    ]

    return {
        "by_category": by_category,
        "stock_distribution": stock_distribution,
        "top_stock": top_stock,
        "status_distribution": status_distribution,
    }


@router.get("/")
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    query = select(Product)
    count_query = select(func.count()).select_from(Product)

    if search:
        pattern = f"%{search}%"
        query = query.where(Product.nome.ilike(pattern))
        count_query = count_query.where(Product.nome.ilike(pattern))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    offset = (page - 1) * limit
    query = query.order_by(Product.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()

    return {"products": [_product_to_dict(p) for p in products], "total": total, "page": page}


@router.post("/", status_code=201)
async def create_product(
    nome: str = Form(...),
    descricao: str = Form(...),
    preco: float = Form(...),
    estoque: int = Form(...),
    categoria: str = Form(...),
    is_active: bool = Form(True),
    imagem: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    try:
        cat = CategoryEnum(categoria)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Categoria inválida: {categoria}")

    imagem_url = None
    if imagem and imagem.filename:
        imagem_url = await _save_image(imagem)

    product = Product(
        nome=nome,
        descricao=descricao,
        preco=preco,
        estoque=estoque,
        categoria=cat,
        is_active=is_active,
        imagem_url=imagem_url,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return _product_to_dict(product)


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    nome: str = Form(...),
    descricao: str = Form(...),
    preco: float = Form(...),
    estoque: int = Form(...),
    categoria: str = Form(...),
    is_active: bool = Form(True),
    imagem: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    try:
        cat = CategoryEnum(categoria)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Categoria inválida: {categoria}")

    product.nome = nome
    product.descricao = descricao
    product.preco = preco
    product.estoque = estoque
    product.categoria = cat
    product.is_active = is_active

    if imagem and imagem.filename:
        product.imagem_url = await _save_image(imagem)

    await db.commit()
    await db.refresh(product)
    return _product_to_dict(product)


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    await db.delete(product)
    await db.commit()
    return {"message": "Produto excluído com sucesso"}

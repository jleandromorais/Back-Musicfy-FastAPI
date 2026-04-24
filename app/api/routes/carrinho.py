from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.models.cart import Cart, CartItem
from app.models.product import Product

router = APIRouter(prefix="/carrinho", tags=["Carrinho"])


class ItemPayload(BaseModel):
    productId: int
    quantity: int


class CriarCarrinhoPayload(BaseModel):
    productId: int
    quantity: int
    userId: Optional[int] = None


class MergePayload(BaseModel):
    items: List[ItemPayload]


def _cart_to_dict(cart: Cart) -> dict:
    items = []
    for ci in cart.items:
        p = ci.product
        items.append({
            "productId": p.id,
            "name": p.nome,
            "price": p.preco,
            "img": p.imagem_url or "",
            "quantity": ci.quantity,
        })
    total = sum(i["price"] * i["quantity"] for i in items)
    return {
        "id": cart.id,
        "userId": cart.user_id,
        "items": items,
        "totalPrice": round(total, 2),
    }


async def _get_cart_with_items(cart_id: int, db: AsyncSession) -> Cart:
    result = await db.execute(
        select(Cart)
        .where(Cart.id == cart_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    cart = result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Carrinho não encontrado")
    return cart


@router.post("/criar", status_code=201)
async def criar_carrinho(payload: CriarCarrinhoPayload, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, payload.productId)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    cart = Cart(user_id=payload.userId)
    db.add(cart)
    await db.flush()

    db.add(CartItem(cart_id=cart.id, product_id=payload.productId, quantity=payload.quantity))
    await db.commit()

    cart = await _get_cart_with_items(cart.id, db)
    return {"cartId": cart.id, **_cart_to_dict(cart)}


@router.get("/user/{user_id}")
async def get_cart_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
        .order_by(Cart.created_at.desc())
    )
    cart = result.scalars().first()
    if not cart:
        raise HTTPException(status_code=404, detail="Carrinho não encontrado")
    return _cart_to_dict(cart)


@router.get("/{cart_id}")
async def get_cart(cart_id: int, db: AsyncSession = Depends(get_db)):
    cart = await _get_cart_with_items(cart_id, db)
    return _cart_to_dict(cart)


@router.post("/{cart_id}/adicionar")
async def adicionar_item(cart_id: int, payload: ItemPayload, db: AsyncSession = Depends(get_db)):
    cart = await _get_cart_with_items(cart_id, db)

    existing = next((ci for ci in cart.items if ci.product_id == payload.productId), None)
    if existing:
        existing.quantity += payload.quantity
    else:
        product = await db.get(Product, payload.productId)
        if not product:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        db.add(CartItem(cart_id=cart_id, product_id=payload.productId, quantity=payload.quantity))

    await db.commit()
    cart = await _get_cart_with_items(cart_id, db)
    return _cart_to_dict(cart)


@router.delete("/{cart_id}/remover/{product_id}")
async def remover_item(cart_id: int, product_id: int, db: AsyncSession = Depends(get_db)):
    cart = await _get_cart_with_items(cart_id, db)
    item = next((ci for ci in cart.items if ci.product_id == product_id), None)
    if item:
        await db.delete(item)
        await db.commit()
    cart = await _get_cart_with_items(cart_id, db)
    return _cart_to_dict(cart)


@router.patch("/{cart_id}/incrementar/{product_id}")
async def incrementar(cart_id: int, product_id: int, db: AsyncSession = Depends(get_db)):
    cart = await _get_cart_with_items(cart_id, db)
    item = next((ci for ci in cart.items if ci.product_id == product_id), None)
    if item:
        item.quantity += 1
        await db.commit()
    cart = await _get_cart_with_items(cart_id, db)
    return _cart_to_dict(cart)


@router.patch("/{cart_id}/decrementar/{product_id}")
async def decrementar(cart_id: int, product_id: int, db: AsyncSession = Depends(get_db)):
    cart = await _get_cart_with_items(cart_id, db)
    item = next((ci for ci in cart.items if ci.product_id == product_id), None)
    if item:
        if item.quantity > 1:
            item.quantity -= 1
        else:
            await db.delete(item)
        await db.commit()
    cart = await _get_cart_with_items(cart_id, db)
    return _cart_to_dict(cart)


@router.delete("/{cart_id}/limpar")
async def limpar_carrinho(cart_id: int, db: AsyncSession = Depends(get_db)):
    cart = await _get_cart_with_items(cart_id, db)
    for item in cart.items:
        await db.delete(item)
    await db.commit()
    return {"message": "Carrinho limpo"}


@router.post("/{cart_id}/merge")
async def merge_carts(cart_id: int, payload: MergePayload, db: AsyncSession = Depends(get_db)):
    cart = await _get_cart_with_items(cart_id, db)

    for new_item in payload.items:
        existing = next((ci for ci in cart.items if ci.product_id == new_item.productId), None)
        if existing:
            existing.quantity += new_item.quantity
        else:
            product = await db.get(Product, new_item.productId)
            if product:
                db.add(CartItem(cart_id=cart_id, product_id=new_item.productId, quantity=new_item.quantity))

    await db.commit()
    cart = await _get_cart_with_items(cart_id, db)
    return _cart_to_dict(cart)

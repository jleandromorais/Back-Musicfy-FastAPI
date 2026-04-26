from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.core.database import get_db
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User

router = APIRouter(prefix="/orders", tags=["Orders"])

# Mapeamento backend → frontend (o frontend espera esses valores em uppercase)
_STATUS_TO_FRONTEND = {
    OrderStatus.PENDING:   "PENDING",
    OrderStatus.PAID:      "PROCESSING",
    OrderStatus.SHIPPED:   "SHIPPED",
    OrderStatus.DELIVERED: "DELIVERED",
    OrderStatus.CANCELLED: "CANCELLED",
}

# Mapeamento frontend → backend (para o PATCH)
_STATUS_FROM_FRONTEND = {
    "PENDING":          OrderStatus.PENDING,
    "PROCESSING":       OrderStatus.PAID,
    "SHIPPED":          OrderStatus.SHIPPED,
    "OUT_FOR_DELIVERY": OrderStatus.SHIPPED,
    "DELIVERED":        OrderStatus.DELIVERED,
    "CANCELLED":        OrderStatus.CANCELLED,
}


def _order_to_dto(order: Order) -> dict:
    items = []
    for item in order.items:
        p = item.product
        items.append({
            "productId":    p.id,
            "productName":  p.nome,
            "productImgPath": p.imagem_url or "",
            "quantity":     item.quantity,
            "unitPrice":    item.price_at_purchase,
            "totalPrice":   round(item.price_at_purchase * item.quantity, 2),
        })

    return {
        "id":         order.id,
        "orderDate":  order.created_at.isoformat() if order.created_at else None,
        "totalPrice": order.total,
        "status":     _STATUS_TO_FRONTEND.get(order.status, "PENDING"),
        "items":      items,
    }


async def _get_order_with_items(order_id: int, db: AsyncSession) -> Order:
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order


@router.get("/user/{firebase_uid}")
async def get_orders_by_user(firebase_uid: str, db: AsyncSession = Depends(get_db)):
    # Busca o usuário pelo firebase_uid
    user_result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    result = await db.execute(
        select(Order)
        .where(Order.user_id == user.id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return [_order_to_dto(o) for o in orders]


class StatusUpdate(BaseModel):
    status: str


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    body: StatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    order = await _get_order_with_items(order_id, db)

    new_status = _STATUS_FROM_FRONTEND.get(body.status.upper())
    if not new_status:
        raise HTTPException(status_code=400, detail=f"Status inválido: {body.status}")

    order.status = new_status
    await db.commit()
    return {"message": "Status atualizado", "status": body.status}

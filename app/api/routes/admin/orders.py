from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.core.database import get_db
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User
from app.api.dependencies import get_current_admin

router = APIRouter(prefix="/admin/orders", tags=["Admin Orders"])

_STATUS_LABEL = {
    OrderStatus.PENDING:   "Aguardando pagamento",
    OrderStatus.PAID:      "Pago — em separação",
    OrderStatus.SHIPPED:   "Enviado",
    OrderStatus.DELIVERED: "Entregue",
    OrderStatus.CANCELLED: "Cancelado",
}


def _order_to_dict(order: Order) -> dict:
    items = []
    for item in order.items:
        p = item.product
        items.append({
            "productId":   p.id,
            "productName": p.nome,
            "productImg":  p.imagem_url or "",
            "quantity":    item.quantity,
            "unitPrice":   item.price_at_purchase,
        })
    return {
        "id":             order.id,
        "orderDate":      order.created_at.isoformat() if order.created_at else None,
        "totalPrice":     order.total,
        "status":         order.status.value,
        "statusLabel":    _STATUS_LABEL.get(order.status, order.status.value),
        "shippingAddress": order.shipping_address,
        "customerName":   order.user.nome if order.user else "—",
        "customerEmail":  order.user.email if order.user else "—",
        "items":          items,
    }


@router.get("/")
async def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    query = (
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.user),
        )
    )
    count_query = select(func.count()).select_from(Order)

    if status:
        try:
            st = OrderStatus(status.lower())
            query = query.where(Order.status == st)
            count_query = count_query.where(Order.status == st)
        except ValueError:
            pass

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    offset = (page - 1) * limit
    query = query.order_by(Order.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()

    return {"orders": [_order_to_dict(o) for o in orders], "total": total, "page": page}


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items).selectinload(OrderItem.product), selectinload(Order.user))
    )
    order = result.scalar_one_or_none()
    if not order:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    try:
        order.status = OrderStatus(body.get("status", "").lower())
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Status inválido")

    await db.commit()
    return _order_to_dict(order)

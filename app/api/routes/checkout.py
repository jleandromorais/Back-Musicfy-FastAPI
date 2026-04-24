import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.core.config import settings
from app.models.order import Order, OrderItem, OrderStatus
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.product import Product

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/checkout", tags=["Checkout"])


class CheckoutItem(BaseModel):
    nomeProduto: str
    precoUnitario: float
    quantidade: int


class CheckoutPayload(BaseModel):
    cartId: int
    userId: int
    enderecoId: int
    items: List[CheckoutItem]
    shippingMethod: str
    shippingPrice: float
    totalPrice: float
    metadata: Optional[dict] = None


@router.post("/create-session")
async def create_checkout_session(
    payload: CheckoutPayload,
    db: AsyncSession = Depends(get_db),
):
    # Buscar endereço
    addr_result = await db.execute(select(Address).where(Address.id == payload.enderecoId))
    address = addr_result.scalar_one_or_none()
    if not address:
        raise HTTPException(status_code=404, detail="Endereço não encontrado")

    shipping_address = f"{address.rua}, {address.numero} - {address.bairro}, {address.cidade}/{address.estado}"

    # Montar line items Stripe
    line_items = [
        {
            "price_data": {
                "currency": "brl",
                "product_data": {"name": item.nomeProduto},
                "unit_amount": int(round(item.precoUnitario * 100)),
            },
            "quantity": item.quantidade,
        }
        for item in payload.items
    ]

    if payload.shippingPrice > 0:
        shipping_labels = {
            "padrao": "Envio Padrão (5-7 dias úteis)",
            "expresso": "Envio Expresso (1-3 dias úteis)",
        }
        line_items.append({
            "price_data": {
                "currency": "brl",
                "product_data": {"name": shipping_labels.get(payload.shippingMethod, "Frete")},
                "unit_amount": int(round(payload.shippingPrice * 100)),
            },
            "quantity": 1,
        })

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=f"{settings.FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/checkout",
            metadata={
                "userId": str(payload.userId),
                "cartId": str(payload.cartId),
                "enderecoId": str(payload.enderecoId),
            },
        )
    except stripe.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Criar pedido como PENDING
    order = Order(
        user_id=payload.userId,
        total=payload.totalPrice,
        status=OrderStatus.PENDING,
        shipping_address=shipping_address,
        stripe_session_id=session.id,
    )
    db.add(order)
    await db.flush()

    for item in payload.items:
        result = await db.execute(
            select(Product).where(Product.nome == item.nomeProduto)
        )
        product = result.scalar_one_or_none()
        if product:
            db.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantidade,
                price_at_purchase=item.precoUnitario,
            ))

    await db.commit()
    return {"url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Webhook inválido")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session["id"]

        result = await db.execute(
            select(Order).where(Order.stripe_session_id == session_id)
        )
        order = result.scalar_one_or_none()
        if order:
            order.status = OrderStatus.PAID
            await db.commit()

    return {"received": True}

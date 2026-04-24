import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.product import Product, CategoryEnum

PRODUCTS = [
    {
        "nome": "Fones de Ouvido Sem Fio",
        "descricao": "com Dolby Surround Sound",
        "preco": 145.0,
        "imagem_url": None,
        "categoria": CategoryEnum.FONES,
        "estoque": 50,
    },
    {
        "nome": "Cancelamento de Ruído Pro",
        "descricao": "Isolamento sonoro máximo",
        "preco": 250.0,
        "imagem_url": None,
        "categoria": CategoryEnum.FONES,
        "estoque": 30,
    },
    {
        "nome": "Headset Gamer X",
        "descricao": "para jogadores competitivos",
        "preco": 150.0,
        "imagem_url": None,
        "categoria": CategoryEnum.HEADSETS,
        "estoque": 40,
    },
    {
        "nome": "Fones Esportivos",
        "descricao": "ajuste seguro para vida ativa",
        "preco": 120.0,
        "imagem_url": None,
        "categoria": CategoryEnum.FONES,
        "estoque": 60,
    },
    {
        "nome": "Monitores de Estúdio Pro",
        "descricao": "áudio preciso para criadores",
        "preco": 300.0,
        "imagem_url": None,
        "categoria": CategoryEnum.CAIXAS_SOM,
        "estoque": 20,
    },
    {
        "nome": "Headset Infantil Seguro",
        "descricao": "volume limitado para ouvidos jovens",
        "preco": 80.0,
        "imagem_url": None,
        "categoria": CategoryEnum.HEADSETS,
        "estoque": 35,
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Product))
        existing = result.scalars().all()
        if existing:
            print(f"Banco já tem {len(existing)} produtos. Seed ignorado.")
            return

        for data in PRODUCTS:
            db.add(Product(**data))

        await db.commit()
        print(f"✅ {len(PRODUCTS)} produtos inseridos com sucesso!")


if __name__ == "__main__":
    asyncio.run(seed())

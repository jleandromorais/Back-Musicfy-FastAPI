# test_auth.py (na raiz do projeto)

import asyncio
from app.core.database import AsyncSessionLocal, engine, Base
from app.models import User
from app.core.security import get_password_hash

async def create_tables():
    """Criar tabelas"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_test_user():
    """Criar usuário de teste"""
    async with AsyncSessionLocal() as session:
        user = User(
            email="test@test.com",
            nome="Test User",
            password_hash=get_password_hash("senha123")
        )
        session.add(user)
        await session.commit()
        print("✅ Usuário criado: test@test.com / senha123")

if __name__ == "__main__":
    asyncio.run(create_tables())
    asyncio.run(create_test_user())
"""
Cria ou promove um usuário como admin.
Uso: python create_admin.py
"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User


async def main():
    email = input("E-mail do admin: ").strip()
    password = input("Senha do admin: ").strip()
    nome = input("Nome do admin: ").strip()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            user.is_admin = True
            user.password_hash = get_password_hash(password)
            if nome:
                user.nome = nome
            await db.commit()
            print(f"✓ Usuário '{email}' promovido a admin.")
        else:
            if not nome:
                nome = "Administrador"
            user = User(
                email=email,
                nome=nome,
                password_hash=get_password_hash(password),
                is_admin=True,
                is_active=True,
            )
            db.add(user)
            await db.commit()
            print(f"✓ Admin '{email}' criado com sucesso.")


if __name__ == "__main__":
    asyncio.run(main())

# test_db.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text  # ← IMPORTANTE: Importar text

async def test_connection():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5433/musicfy",
        echo=True
    )
    
    try:
        async with engine.begin() as conn:
            # ✅ USAR text() para queries SQL
            result = await conn.execute(text("SELECT 1"))
            print("✅ Conexão com PostgreSQL OK!")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

asyncio.run(test_connection())
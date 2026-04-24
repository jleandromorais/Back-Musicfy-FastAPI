from app.core.config import settings

print('✅ Config carregado com sucesso!')
print(f'DATABASE_URL: {settings.DATABASE_URL[:30]}...')
print(f'FRONTEND_URL: {settings.FRONTEND_URL}')
print(f'SECRET_KEY: {settings.SECRET_KEY[:20]}...')

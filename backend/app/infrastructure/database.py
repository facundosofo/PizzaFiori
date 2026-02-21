from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote

from app.domain.models.base import Base
from app.infrastructure.config.settings import settings

# Import all models to ensure SQLAlchemy can resolve relationships
import app.domain.models  # noqa: F401

# PostgreSQL connection string with asyncpg driver
# Format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL = f"postgresql+asyncpg://{quote(settings.db_user)}:{quote(settings.db_password)}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

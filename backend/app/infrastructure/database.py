import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote

from app.domain.models.base import Base
from app.infrastructure.config.settings import settings

# Import all models to ensure SQLAlchemy can resolve relationships
import app.domain.models  # noqa: F401

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# PostgreSQL connection string with asyncpg driver
# Format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL = (
    f"postgresql+asyncpg://{quote(settings.db_user, safe='')}:{quote(settings.db_password, safe='')}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={
    "ssl": ssl_context,
    "statement_cache_size": 0,
    "timeout": 10
}
)

AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
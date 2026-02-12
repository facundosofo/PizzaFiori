from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

from app.domain.models.base import Base
from app.infrastructure.config.settings import settings

# Import all models to ensure SQLAlchemy can resolve relationships
import app.domain.models  # noqa: F401

params = quote_plus(
    f"DRIVER={settings.db_driver};SERVER={settings.db_host};DATABASE={settings.db_name};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes"
)

DATABASE_URL = f"mssql+aioodbc:///?odbc_connect={params}"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

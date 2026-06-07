from sqlalchemy import Column, Integer, String, Numeric

from app.domain.models.base import Base


class AppConfig(Base):
    __tablename__ = "app_config"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<AppConfig(key={self.key}, value={self.value})>"
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.domain.models.base import Base

class Category(Base):
    __tablename__ = "Categorias"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)

    productos = relationship(
        "Product",
        back_populates="categoria"
    )

    oferta_items = relationship(
        "OfferItem",
        back_populates="categoria"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, nombre={self.nombre})>"

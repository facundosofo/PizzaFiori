from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.domain.models.base import Base

class ProductCategory(Base):
    __tablename__ = "productos_categorias"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now, nullable=False)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    productos = relationship(
        "Product",
        back_populates="categoria"
    )

    oferta_items = relationship(
        "OfferItem",
        back_populates="categoria"
    )

    stock = relationship(
        "CategoryStock",
        back_populates="categoria",
        uselist=False,
    )

    def __repr__(self):
        return f"<ProductCategory(id={self.id}, nombre={self.nombre})>"

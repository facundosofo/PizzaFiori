from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.domain.models.base import Base


class CategoryStock(Base):
    __tablename__ = "stock_categorias"

    categoria_id = Column(
        Integer, ForeignKey("productos_categorias.id"), primary_key=True
    )
    cantidad = Column(Numeric(10, 3), nullable=False, default=0)
    umbral_amarillo = Column(Integer, nullable=True)
    umbral_rojo = Column(Integer, nullable=True)
    fecha_actualizacion = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    categoria = relationship("ProductCategory", back_populates="stock")

    def __repr__(self):
        return f"<CategoryStock(categoria_id={self.categoria_id}, cantidad={self.cantidad})>"

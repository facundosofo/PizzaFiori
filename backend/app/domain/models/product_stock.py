from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.domain.models.base import Base


class ProductStock(Base):
    __tablename__ = "stock_productos"

    producto_id = Column(
        Integer, ForeignKey("Productos.id", ondelete="CASCADE"), primary_key=True
    )
    cantidad = Column(Numeric(10, 3), nullable=False, default=0)
    umbral_amarillo = Column(Integer, nullable=True)
    umbral_rojo = Column(Integer, nullable=True)
    fecha_actualizacion = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    producto = relationship("Product", back_populates="stock")

    def __repr__(self):
        return f"<ProductStock(producto_id={self.producto_id}, cantidad={self.cantidad})>"

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, Numeric, DateTime, Index
from sqlalchemy.orm import relationship

from app.domain.models.base import Base

class ProductPrice(Base):
    __tablename__ = "ProductoPrecios"
    __table_args__ = (
        # Índice compuesto para optimizar búsquedas de precio por cantidad
        Index('ix_productoprecio_producto_cantidad', 'producto_id', 'cantidad'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    producto_id = Column(Integer, ForeignKey("Productos.id"), nullable=False)
    cantidad = Column(Numeric(10, 3), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now)

    producto = relationship(
        "Product",
        back_populates="precios"
    )

    def __repr__(self):
        return (
            f"<ProductPrice(producto_id={self.producto_id}, "
            f"cantidad={self.cantidad}, precio={self.precio})>"
        )

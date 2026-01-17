from sqlalchemy import Column, ForeignKey, Integer, Numeric, DateTime
from sqlalchemy.orm import relationship
from app.infrastructure.database import Base
from datetime import datetime

class ProductPrice(Base):
    __tablename__ = "ProductPrices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    producto_id = Column(Integer, ForeignKey("Productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
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

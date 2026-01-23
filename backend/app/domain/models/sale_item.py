from sqlalchemy import Column, Integer, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.orm import relationship

from app.domain.models.base import Base


class SaleItem(Base):
    __tablename__ = "VentaItems"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    venta_id = Column(Integer, ForeignKey("Ventas.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("Productos.id"), nullable=True)
    oferta_id = Column(Integer, ForeignKey("Ofertas.id"), nullable=True)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "(producto_id IS NOT NULL AND oferta_id IS NULL) OR (producto_id IS NULL AND oferta_id IS NOT NULL)",
            name="check_producto_or_oferta"
        ),
    )

    venta = relationship(
        "Sale",
        back_populates="items"
    )

    producto = relationship(
        "Product",
        foreign_keys=[producto_id]
    )

    oferta = relationship(
        "Offer",
        foreign_keys=[oferta_id]
    )

    def __repr__(self):
        return (
            f"<SaleItem(id={self.id}, venta_id={self.venta_id}, "
            f"producto_id={self.producto_id}, oferta_id={self.oferta_id}, "
            f"cantidad={self.cantidad}, subtotal={self.subtotal})>"
        )

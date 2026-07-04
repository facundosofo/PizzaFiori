from sqlalchemy import Column, Integer, ForeignKey, String, Index, Numeric
from sqlalchemy.orm import relationship

from app.domain.models.base import Base


class SaleItemOfferProduct(Base):
    """Snapshot de productos incluidos en una oferta al momento de la venta.
    
    Esta tabla preserva qué productos componían una oferta cuando se realizó la venta,
    permitiendo mantener el historial incluso si la oferta cambia después.
    """
    __tablename__ = "VentaItemOfertaProductos"
    __table_args__ = (
        # Índice simple para JOINs y operaciones WHERE en dashboard
        Index('ix_ventaitemofertaproductos_venta_item_id', 'venta_item_id'),
        # Índices compuestos para optimizar queries del dashboard
        Index('ix_ventaitemofertaproductos_ventaitem_producto', 'venta_item_id', 'producto_id'),
        Index('ix_ventaitemofertaproductos_categoria_nombre', 'categoria_nombre'),
        Index('ix_ventaitemofertaproductos_producto_nombre', 'producto_nombre'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    venta_item_id = Column(Integer, ForeignKey("VentaItems.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(Integer, ForeignKey("Productos.id"), nullable=True)  # Referencia (puede ser null si se borra)
    producto_nombre = Column(String(50), nullable=False)  # Nombre guardado al momento de la venta
    categoria_nombre = Column(String(50), nullable=True)  # Categoría del producto en la oferta
    cantidad = Column(Numeric(10, 3), nullable=False)  # Cantidad de este producto en la oferta

    venta_item = relationship(
        "SaleItem",
        back_populates="oferta_productos_snapshot"
    )

    producto = relationship(
        "Product",
        foreign_keys=[producto_id]
    )

    def __repr__(self):
        return (
            f"<SaleItemOfferProduct(id={self.id}, venta_item_id={self.venta_item_id}, "
            f"producto_nombre={self.producto_nombre}, cantidad={self.cantidad})>"
        )

from sqlalchemy import Column, Integer, ForeignKey, Numeric, CheckConstraint, String, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.domain.models.base import Base


class SaleItem(Base):
    __tablename__ = "VentaItems"
    __table_args__ = (
        CheckConstraint(
            "(producto_id IS NOT NULL AND oferta_id IS NULL) OR (producto_id IS NULL AND oferta_id IS NOT NULL)",
            name="check_producto_or_oferta"
        ),
        # Índices compuestos para optimizar queries del dashboard
        Index('ix_ventaitems_venta_producto', 'venta_id', 'producto_id'),
        Index('ix_ventaitems_venta_oferta', 'venta_id', 'oferta_id'),
        Index('ix_ventaitems_item_categoria', 'item_categoria'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    venta_id = Column(Integer, ForeignKey("Ventas.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("Productos.id"), nullable=True)
    oferta_id = Column(Integer, ForeignKey("Ofertas.id"), nullable=True)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    
    # Referencia de negocio (inmutable) - solo para productos
    producto_sku = Column(String(50), nullable=True, index=True)  # SKU del producto
    
    # Campos de snapshot para preservar información histórica
    item_nombre = Column(String(255), nullable=False)  # Nombre del producto/oferta al momento de la venta
    item_categoria = Column(String(100), nullable=False)  # Categoría al momento de la venta
    item_descripcion = Column(Text, nullable=True)  # Descripción de la oferta (si aplica)

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
    
    # Snapshot de productos que componían la oferta al momento de la venta
    oferta_productos_snapshot = relationship(
        "SaleItemOfferProduct",
        back_populates="venta_item",
        cascade="all, delete-orphan"
    )

    @hybrid_property
    def producto_nombre(self) -> str | None:
        """Retorna el nombre del producto si existe."""
        return self.producto.nombre if self.producto else None

    @hybrid_property
    def oferta_nombre(self) -> str | None:
        """Retorna el nombre de la oferta si existe."""
        return self.oferta.nombre if self.oferta else None

    def __repr__(self):
        return (
            f"<SaleItem(id={self.id}, venta_id={self.venta_id}, "
            f"producto_id={self.producto_id}, oferta_id={self.oferta_id}, "
            f"cantidad={self.cantidad}, subtotal={self.subtotal})>"
        )


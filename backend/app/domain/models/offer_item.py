from sqlalchemy import Column, ForeignKey, Integer, Numeric, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.domain.models.base import Base

# Tabla junction para relación many-to-many entre OfferItem y Product
# Un item puede tener 1 o N productos (opciones)
oferta_item_productos = Table(
    'OfertaItemProductos',
    Base.metadata,
    Column('oferta_item_id', Integer, ForeignKey('OfertaItems.id', ondelete='CASCADE'), primary_key=True),
    Column('producto_id', Integer, ForeignKey('Productos.id', ondelete='CASCADE'), primary_key=True)
)

class OfferItem(Base):
    __tablename__ = "OfertaItems"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    oferta_id = Column(Integer, ForeignKey("Ofertas.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("productos_categorias.id"), nullable=True)
    cantidad = Column(Numeric(10, 3), nullable=False, default=1)

    oferta = relationship(
        "Offer",
        back_populates="productos"
    )

    # Relación many-to-many con productos (siempre usa tabla intermedia)
    productos = relationship(
        "Product",
        secondary=oferta_item_productos,
        lazy="selectin"
    )

    categoria = relationship(
        "ProductCategory",
        back_populates="oferta_items",
        lazy="selectin"
    )

    @hybrid_property
    def categoria_nombre(self):
        """Retorna el nombre de la categoría si existe."""
        return self.categoria.nombre if self.categoria else None

    def __repr__(self):
        return (
            f"<OfferItem(oferta_id={self.oferta_id}, "
            f"categoria_id={self.categoria_id}, cantidad={self.cantidad})>"
        )

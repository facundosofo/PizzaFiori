from sqlalchemy import Column, ForeignKey, Integer, Table
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
    categoria_id = Column(Integer, ForeignKey("Categorias.id"), nullable=True)
    cantidad = Column(Integer, nullable=False, default=1)

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
        "Category",
        back_populates="oferta_items"
    )

    def __repr__(self):
        return (
            f"<OfferItem(oferta_id={self.oferta_id}, "
            f"categoria_id={self.categoria_id}, cantidad={self.cantidad})>"
        )

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.domain.models.base import Base

class OfferItem(Base):
    __tablename__ = "OfertaItems"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    oferta_id = Column(Integer, ForeignKey("Ofertas.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("Productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)

    oferta = relationship(
        "Offer",
        back_populates="productos"
    )

    producto = relationship(
        "Product",
        back_populates="ofertas"
    )

    @hybrid_property
    def producto_nombre(self) -> str | None:
        """Retorna el nombre del producto si existe."""
        return self.producto.nombre if self.producto else None

    def __repr__(self):
        return (
            f"<OfferItem(oferta_id={self.oferta_id}, "
            f"producto_id={self.producto_id}, cantidad={self.cantidad})>"
        )

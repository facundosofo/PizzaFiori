from datetime import datetime

from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.domain.models.base import Base

class Offer(Base):
    __tablename__ = "Ofertas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String, nullable=True)
    precio = Column(Numeric(10, 2), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now)

    productos = relationship(
        "OfferItem",
        back_populates="oferta",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Offer(nombre={self.nombre}, precio={self.precio})>"

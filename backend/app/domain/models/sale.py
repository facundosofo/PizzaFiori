from datetime import datetime

from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.orm import relationship

from app.domain.models.base import Base


class Sale(Base):
    __tablename__ = "Ventas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    numero_orden = Column(String(17), nullable=True, unique=True)
    total = Column(Numeric(10, 2), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.now, index=True)  # Índice para filtros de fecha en dashboard
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    items = relationship(
        "SaleItem",
        back_populates="venta",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Sale(id={self.id}, numero_orden={self.numero_orden}, total={self.total})>"

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.domain.models.base import Base

class Product(Base):
    __tablename__ = "Productos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    categoria_id = Column(Integer, ForeignKey("Categorias.id"), nullable=True)
    imagen = Column(String(255), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now)

    categoria = relationship(
        "Category",
        back_populates="productos"
    )

    precios = relationship(
        "ProductPrice",
        back_populates="producto",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Product(id={self.id}, nombre={self.nombre})>"

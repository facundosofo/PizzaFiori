from sqlalchemy import Column, ForeignKey, Integer, String, Numeric, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.infrastructure.database import Base
from app.domain.category import Categoria
from datetime import datetime

class Producto(Base):
    __tablename__ = "Productos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=True)
    precio_venta = Column(Numeric(10,2), nullable=False)
    categoria_id = Column(Integer, ForeignKey("Categorias.id"), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)

    categoria = relationship("Categoria")

def __repr__(self):
    return f"<Producto(nombre={self.nombre}, precio={self.precio_venta})>"
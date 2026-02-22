from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, Index
from sqlalchemy.orm import relationship

from app.domain.models.base import Base


class ExpenseCategory(Base):
    __tablename__ = "gastos_categorias"
    __table_args__ = (
        # Índice en padre_id para optimizar consultas de jerarquía
        Index('ix_gastos_categorias_padre', 'padre_id'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, index=True)
    descripcion = Column(String(255), nullable=True)
    padre_id = Column(Integer, ForeignKey("gastos_categorias.id"), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now, nullable=False)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Relación autorreferencial para subcategorías
    # Usar single_parent=True para permitir delete-orphan en cascada
    subcategorias = relationship(
        "ExpenseCategory",
        back_populates="padre_categoria",
        cascade="all, delete-orphan",
        single_parent=True
    )

    # Relación inversa para acceder al padre
    padre_categoria = relationship(
        "ExpenseCategory",
        back_populates="subcategorias",
        remote_side=[id]
    )

    # Relación con gastos
    gastos = relationship(
        "Expense",
        back_populates="categoria_gasto"
    )

    def __repr__(self):
        return f"<ExpenseCategory(id={self.id}, nombre={self.nombre})>"

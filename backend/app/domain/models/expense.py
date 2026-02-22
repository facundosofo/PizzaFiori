from datetime import datetime, date

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, Date, Numeric, Index
from sqlalchemy.orm import relationship

from app.domain.models.base import Base


class Expense(Base):
    __tablename__ = "gastos"
    __table_args__ = (
        # Índices para optimizar filtrados y JOINs
        Index('ix_gastos_categoria', 'categoria_gasto_id'),
        Index('ix_gastos_fecha', 'fecha_pago'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    categoria_gasto_id = Column(Integer, ForeignKey("gastos_categorias.id"), nullable=False)
    descripcion = Column(String(500), nullable=True)
    monto = Column(Numeric(12, 2), nullable=False)
    fecha_pago = Column(Date, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now, nullable=False)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Relación con categoría de gastos
    categoria_gasto = relationship(
        "ExpenseCategory",
        back_populates="gastos"
    )

    def __repr__(self):
        return f"<Expense(id={self.id}, monto={self.monto})>"

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.domain.models.base import Base


class AuditLog(Base):
    """
    Modelo para auditoría de acciones del sistema.
    Registra quién hizo qué, sobre qué entidad, cuándo y qué cambió.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)
    
    # Quién realizó la acción
    user_id = Column(Integer, ForeignKey("Usuarios.id"), nullable=False, index=True)
    user = relationship("User", foreign_keys=[user_id])
    
    # Sobre qué entidad
    entity_type = Column(String(50), nullable=False, index=True)  # "Product", "User", "Sale", etc.
    entity_id = Column(Integer, nullable=False, index=True)
    
    # Qué acción
    action = Column(String(20), nullable=False)  # "CREATE", "UPDATE", "DELETE"
    
    # Qué cambió (diff completo: old/new values)
    changes = Column(JSONB, nullable=False)
    
    # Contexto adicional
    correlation_id = Column(String(36), nullable=True, index=True)  # UUID del request
    
    # Índices compuestos para optimizar queries comunes
    __table_args__ = (
        Index('ix_audit_entity_timestamp', 'entity_type', 'entity_id', 'timestamp'),
        Index('ix_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_audit_timestamp_desc', timestamp.desc()),
    )

    def __repr__(self):
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"action={self.action}, entity={self.entity_type}:{self.entity_id})>"
        )

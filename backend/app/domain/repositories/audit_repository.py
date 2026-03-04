from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.domain.models.audit_log import AuditLog


class AbstractAuditRepository(ABC):
    """
    Repositorio abstracto para operaciones de auditoría.
    """
    
    @abstractmethod
    async def log_action(
        self,
        username: str,
        entity_type: str,
        entity_id: int,
        action: str,
        changes: dict,
    ) -> AuditLog:
        """
        Registra una acción de auditoría.
        
        Args:
            username: Nombre de usuario que realizó la acción
            entity_type: Tipo de entidad (Product, User, Sale, etc.)
            entity_id: ID de la entidad afectada
            action: Acción realizada (CREATE, UPDATE, DELETE)
            changes: Diccionario con los cambios (formato: {"field": {"old": val, "new": val}})
        
        Returns:
            AuditLog creado
        """
        ...



    @abstractmethod
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_type: Optional[str] = None,
        username: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """
        Obtiene registros de auditoría en un rango de fechas.
        
        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            entity_type: Filtrar por tipo de entidad (opcional)
            username: Filtrar por usuario (opcional)
            action: Filtrar por tipo de acción (opcional)
            limit: Número máximo de registros
            offset: Número de registros a omitir
        
        Returns:
            Lista de registros de auditoría ordenados por timestamp DESC
        """
        ...

    
    @abstractmethod
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 50,
    ) -> List[AuditLog]:
        """Obtiene registros de auditoría filtrados por tipo y ID de entidad."""
        ...

    @abstractmethod
    async def count(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        entity_type: Optional[str] = None,
        username: Optional[str] = None,
        action: Optional[str] = None,
    ) -> int:
        """
        Cuenta el número total de registros de auditoría con filtros.
        
        Args:
            start_date: Fecha inicial (opcional)
            end_date: Fecha final (opcional)
            entity_type: Filtrar por tipo de entidad (opcional)
            username: Filtrar por usuario (opcional)
            action: Filtrar por tipo de acción (opcional)
        
        Returns:
            Número total de registros
        """
        ...

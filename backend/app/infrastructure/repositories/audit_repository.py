from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.audit_log import AuditLog
from app.domain.repositories.audit_repository import AbstractAuditRepository
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyAuditRepository(
    BaseRepository[AuditLog], AbstractAuditRepository
):
    """
    Implementación concreta del repositorio de auditoría usando SQLAlchemy.
    """
    model = AuditLog

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def log_action(
        self,
        user_id: int,
        entity_type: str,
        entity_id: int,
        action: str,
        changes: dict,
        ip_address: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> AuditLog:
        """
        Registra una acción de auditoría en la base de datos.
        """
        audit_log = AuditLog(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=changes,
            ip_address=ip_address,
            correlation_id=correlation_id,
            timestamp=datetime.now(),
        )
        
        return await self.add(audit_log)

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditLog]:
        """
        Obtiene el historial de auditoría de una entidad específica.
        Incluye información del usuario que realizó la acción.
        """
        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == entity_id,
                )
            )
            .options(selectinload(AuditLog.user))
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditLog]:
        """
        Obtiene todas las acciones realizadas por un usuario.
        """
        query = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .options(selectinload(AuditLog.user))
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_type: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """
        Obtiene registros de auditoría en un rango de fechas con filtros opcionales.
        """
        conditions = [
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date,
        ]
        
        if entity_type is not None:
            conditions.append(AuditLog.entity_type == entity_type)
        
        if user_id is not None:
            conditions.append(AuditLog.user_id == user_id)
        
        query = (
            select(AuditLog)
            .where(and_(*conditions))
            .options(selectinload(AuditLog.user))
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_recent(
        self,
        limit: int = 100,
        entity_type: Optional[str] = None,
    ) -> List[AuditLog]:
        """
        Obtiene los registros de auditoría más recientes del sistema.
        """
        query = select(AuditLog).options(selectinload(AuditLog.user))
        
        if entity_type is not None:
            query = query.where(AuditLog.entity_type == entity_type)
        
        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(
        self,
        entity_type: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> int:
        """
        Cuenta el número total de registros de auditoría con filtros opcionales.
        """
        query = select(func.count()).select_from(AuditLog)
        
        conditions = []
        if entity_type is not None:
            conditions.append(AuditLog.entity_type == entity_type)
        
        if user_id is not None:
            conditions.append(AuditLog.user_id == user_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar() or 0

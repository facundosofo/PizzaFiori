from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

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
        username: str,
        entity_type: str,
        entity_id: int,
        action: str,
        changes: dict,
    ) -> AuditLog:
        """
        Registra una acción de auditoría en la base de datos.
        """
        audit_log = AuditLog(
            username=username,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=_normalize_json_value(changes),
            timestamp=datetime.now(),
        )
        
        return await self.add(audit_log)


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
        Obtiene registros de auditoría en un rango de fechas con filtros opcionales.
        """
        conditions = [
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date,
        ]
        
        if entity_type is not None:
            conditions.append(AuditLog.entity_type == entity_type)
        
        if username is not None:
            conditions.append(AuditLog.username == username)
        
        if action is not None:
            conditions.append(AuditLog.action == action)
        
        query = (
            select(AuditLog)
            .where(and_(*conditions))
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 50,
    ) -> List[AuditLog]:
        """Obtiene registros de auditoría filtrados por tipo y ID de entidad."""
        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == entity_id,
                )
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        entity_type: Optional[str] = None,
        username: Optional[str] = None,
        action: Optional[str] = None,
    ) -> int:
        """
        Cuenta el número total de registros de auditoría con filtros opcionales.
        """
        query = select(func.count()).select_from(AuditLog)
        
        conditions = []
        if start_date is not None:
            conditions.append(AuditLog.timestamp >= start_date)
        
        if end_date is not None:
            conditions.append(AuditLog.timestamp <= end_date)
        
        if entity_type is not None:
            conditions.append(AuditLog.entity_type == entity_type)
        
        if username is not None:
            conditions.append(AuditLog.username == username)
        
        if action is not None:
            conditions.append(AuditLog.action == action)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar() or 0


def _normalize_json_value(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, dict):
        return {key: _normalize_json_value(inner_value) for key, inner_value in value.items()}

    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]

    if isinstance(value, tuple):
        return [_normalize_json_value(item) for item in value]

    if isinstance(value, (int, float, str, bool)):
        return value

    return str(value)

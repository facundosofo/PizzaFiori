"""
Servicio para gestión de auditoría de acciones del sistema.
"""
from dataclasses import dataclass
from typing import Any, Optional, List
from datetime import datetime
import structlog

from app.domain.unit_of_work import AbstractUnitOfWork
from app.domain.models.audit_log import AuditLog
from app.application.utils.audit_helpers import (
    compute_entity_diff,
    compute_sale_diff,
    entity_to_snapshot,
    sale_to_snapshot,
)


@dataclass
class AuditServiceResult:
    """Resultado de operaciones del servicio de auditoría."""
    value: Optional[Any] = None
    error: Optional[str] = None
    status_code: int = 200


class AuditService:
    """
    Servicio para registro y consulta de auditoría de acciones.
    
    Responsabilidades:
    - Registrar operaciones CREATE, UPDATE, DELETE sobre entidades
    - Generar diffs automáticos de cambios
    - Consultar historial de auditoría
    """
    
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        logger: structlog.BoundLogger | None = None
    ):
        self.uow = uow
        self.logger = logger or structlog.get_logger(__name__)
    
    async def log_creation(
        self,
        username: str,
        entity_type: str,
        entity: Any,
    ) -> AuditServiceResult:
        """
        Registra la creación de una entidad.
        
        Args:
            username: Username del usuario (para referencia permanente)
            entity_type: Tipo de entidad (Product, User, Sale, etc.)
            entity: Instancia de la entidad creada
        
        Returns:
            AuditServiceResult con el log de auditoría creado
        """
        try:
            # Para creación, capturar snapshot completo como "new" values
            if entity_type == "Sale":
                snapshot = sale_to_snapshot(entity)
            else:
                snapshot = entity_to_snapshot(entity)
            
            changes = {"new": snapshot}
            
            entity_id = getattr(entity, 'id', None)
            if entity_id is None:
                return AuditServiceResult(
                    error="Entity does not have an ID",
                    status_code=400
                )
            
            async with self.uow as uow:
                audit_log = await uow.audit_repo.log_action(
                    username=username,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    action="CREATE",
                    changes=changes,
                )
                await uow.commit()
            
            self.logger.info(
                "Auditoría de creación registrada",
                audit_id=audit_log.id,
                entity_type=entity_type,
                entity_id=entity_id,
            )
            
            return AuditServiceResult(value=audit_log, status_code=201)
        
        except Exception as e:
            self.logger.error(
                "Error al registrar auditoría de creación",
                error=str(e),
                entity_type=entity_type,
                exc_info=True
            )
            return AuditServiceResult(
                error=f"Error registrando auditoría: {str(e)}",
                status_code=500
            )
    
    async def log_update(
        self,
        username: str,
        entity_type: str,
        old_entity: Any,
        new_entity: Any,
    ) -> AuditServiceResult:
        """
        Registra la actualización de una entidad.
        
        Args:
            username: Username del usuario (para referencia permanente)
            entity_type: Tipo de entidad
            old_entity: Instancia anterior de la entidad (antes del cambio)
            new_entity: Instancia nueva de la entidad (después del cambio)
        
        Returns:
            AuditServiceResult con el log de auditoría creado
        """
        try:
            # Generar diff según el tipo de entidad
            if entity_type == "Sale":
                diff = compute_sale_diff(old_entity, new_entity)
            else:
                diff = compute_entity_diff(old_entity, new_entity)
            
            # Si no hay cambios, no registrar nada
            if not diff:
                self.logger.debug(
                    "No hay cambios para auditar",
                    entity_type=entity_type,
                )
                return AuditServiceResult(value=None, status_code=200)
            
            entity_id = getattr(new_entity, 'id', None)
            if entity_id is None:
                return AuditServiceResult(
                    error="Entity does not have an ID",
                    status_code=400
                )
            
            async with self.uow as uow:
                audit_log = await uow.audit_repo.log_action(
                    username=username,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    action="UPDATE",
                    changes=diff,
                )
                await uow.commit()
            
            self.logger.info(
                "Auditoría de actualización registrada",
                audit_id=audit_log.id,
                entity_type=entity_type,
                entity_id=entity_id,
                fields_changed=list(diff.keys()),
            )
            
            return AuditServiceResult(value=audit_log, status_code=201)
        
        except Exception as e:
            self.logger.error(
                "Error al registrar auditoría de actualización",
                error=str(e),
                entity_type=entity_type,
                exc_info=True
            )
            return AuditServiceResult(
                error=f"Error registrando auditoría: {str(e)}",
                status_code=500
            )
    
    async def log_deletion(
        self,
        username: str,
        entity_type: str,
        entity: Any,
    ) -> AuditServiceResult:
        """
        Registra la eliminación de una entidad.
        
        Args:
            username: Username del usuario (para referencia permanente)
            entity_type: Tipo de entidad
            entity: Instancia de la entidad antes de ser eliminada
        
        Returns:
            AuditServiceResult con el log de auditoría creado
        """
        try:
            # Para eliminación, capturar snapshot completo como "old" values
            if entity_type == "Sale":
                snapshot = sale_to_snapshot(entity)
            else:
                snapshot = entity_to_snapshot(entity)
            
            changes = {"old": snapshot}
            
            entity_id = getattr(entity, 'id', None)
            if entity_id is None:
                return AuditServiceResult(
                    error="Entity does not have an ID",
                    status_code=400
                )
            
            async with self.uow as uow:
                audit_log = await uow.audit_repo.log_action(
                    username=username,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    action="DELETE",
                    changes=changes,
                )
                await uow.commit()
            
            self.logger.info(
                "Auditoría de eliminación registrada",
                audit_id=audit_log.id,
                entity_type=entity_type,
                entity_id=entity_id,
            )
            
            return AuditServiceResult(value=audit_log, status_code=201)
        
        except Exception as e:
            self.logger.error(
                "Error al registrar auditoría de eliminación",
                error=str(e),
                entity_type=entity_type,
                exc_info=True
            )
            return AuditServiceResult(
                error=f"Error registrando auditoría: {str(e)}",
                status_code=500
            )
    
    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditServiceResult:
        """
        Obtiene el historial completo de auditoría de una entidad.
        
        Args:
            entity_type: Tipo de entidad
            entity_id: ID de la entidad
            limit: Número máximo de registros
            offset: Número de registros a omitir
        
        Returns:
            AuditServiceResult con lista de AuditLogs
        """
        try:
            async with self.uow as uow:
                audit_logs = await uow.audit_repo.get_by_entity(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    limit=limit,
                    offset=offset,
                )
            
            self.logger.debug(
                "Historial de entidad obtenido",
                entity_type=entity_type,
                entity_id=entity_id,
                records_count=len(audit_logs),
            )
            
            return AuditServiceResult(value=audit_logs, status_code=200)
        
        except Exception as e:
            self.logger.error(
                "Error al obtener historial de entidad",
                error=str(e),
                entity_type=entity_type,
                entity_id=entity_id,
                exc_info=True
            )
            return AuditServiceResult(
                error=f"Error obteniendo historial: {str(e)}",
                status_code=500
            )
    
    async def get_user_actions(
        self,
        username: str,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditServiceResult:
        """
        Obtiene todas las acciones realizadas por un usuario.
        
        Args:
            username: Username del usuario
            limit: Número máximo de registros
            offset: Número de registros a omitir
        
        Returns:
            AuditServiceResult con lista de AuditLogs
        """
        try:
            async with self.uow as uow:
                audit_logs = await uow.audit_repo.get_by_username(
                    username=username,
                    limit=limit,
                    offset=offset,
                )
            
            self.logger.debug(
                "Acciones de usuario obtenidas",
                username=username,
                records_count=len(audit_logs),
            )
            
            return AuditServiceResult(value=audit_logs, status_code=200)
        
        except Exception as e:
            self.logger.error(
                "Error al obtener acciones de usuario",
                error=str(e),
                username=username,
                exc_info=True
            )
            return AuditServiceResult(
                error=f"Error obteniendo acciones: {str(e)}",
                status_code=500
            )
    
    async def get_recent_activity(
        self,
        limit: int = 100,
        entity_type: Optional[str] = None,
    ) -> AuditServiceResult:
        """
        Obtiene la actividad reciente del sistema.
        
        Args:
            limit: Número máximo de registros
            entity_type: Filtrar por tipo de entidad (opcional)
        
        Returns:
            AuditServiceResult con lista de AuditLogs
        """
        try:
            async with self.uow as uow:
                audit_logs = await uow.audit_repo.get_recent(
                    limit=limit,
                    entity_type=entity_type,
                )
            
            self.logger.debug(
                "Actividad reciente obtenida",
                records_count=len(audit_logs),
                entity_type=entity_type,
            )
            
            return AuditServiceResult(value=audit_logs, status_code=200)
        
        except Exception as e:
            self.logger.error(
                "Error al obtener actividad reciente",
                error=str(e),
                exc_info=True
            )
            return AuditServiceResult(
                error=f"Error obteniendo actividad: {str(e)}",
                status_code=500
            )
    
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_type: Optional[str] = None,
        username: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AuditServiceResult:
        """
        Obtiene registros de auditoría en un rango de fechas.
        
        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            entity_type: Filtrar por tipo de entidad (opcional)
            username: Filtrar por usuario (opcional)
            action: Filtrar por tipo de acción (CREATE, UPDATE, DELETE) (opcional)
            limit: Número máximo de registros
            offset: Número de registros a omitir
        
        Returns:
            AuditServiceResult con lista de AuditLogs
        """
        try:
            async with self.uow as uow:
                audit_logs = await uow.audit_repo.get_by_date_range(
                    start_date=start_date,
                    end_date=end_date,
                    entity_type=entity_type,
                    username=username,
                    action=action,
                    limit=limit,
                    offset=offset,
                )
            
            self.logger.debug(
                "Auditoría por rango de fechas obtenida",
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                records_count=len(audit_logs),
            )
            
            return AuditServiceResult(value=audit_logs, status_code=200)
        
        except Exception as e:
            self.logger.error(
                "Error al obtener auditoría por rango de fechas",
                error=str(e),
                exc_info=True
            )
            return AuditServiceResult(
                error=f"Error obteniendo auditoría: {str(e)}",
                status_code=500
            )

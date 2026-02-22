from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, date
import structlog

from app.domain.models.expense import Expense
from app.domain.unit_of_work import AbstractUnitOfWork
from app.infrastructure.cache.cache_service import CacheService
from app.presentation.schemas.expense_schemas import (
    GastoCreateRequest,
    GastoUpdateRequest,
)


@dataclass
class ServiceResult:
    value: Optional[Expense] = None
    error: Optional[str] = None
    status_code: int = 200


class ExpenseService:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        cache_service: CacheService,
        audit_service=None,
        logger: structlog.BoundLogger | None = None,
    ):
        self.uow = uow
        self.cache_service = cache_service
        self.audit_service = audit_service
        self.logger = logger or structlog.get_logger(__name__)

    async def create(
        self,
        gasto_create: GastoCreateRequest,
        username: str,
    ) -> ServiceResult:
        try:
            self.logger.debug(
                "Creando gasto",
                monto=gasto_create.monto,
            )

            async with self.uow as uow:
                # Validar que categoría existe
                categoria = await uow.expense_category_repo.get_by_id(
                    gasto_create.categoria_gasto_id
                )
                if not categoria:
                    return ServiceResult(
                        error="Categoría de gasto no encontrada", status_code=404
                    )

                gasto = Expense(
                    categoria_gasto_id=gasto_create.categoria_gasto_id,
                    descripcion=gasto_create.descripcion,
                    monto=gasto_create.monto,
                    fecha_pago=gasto_create.fecha_pago,
                    activo=True,
                    fecha_creacion=datetime.now(),
                    fecha_actualizacion=datetime.now(),
                )

                await uow.expense_repo.add(gasto)
                await uow.commit()
                await uow.expense_repo.refresh(gasto)

                # Auditar creación
                if self.audit_service:
                    await self.audit_service.log_creation(
                        username=username,
                        entity_type="Expense",
                        entity=gasto,
                    )

                self.logger.debug(
                    "Gasto creado exitosamente",
                    gasto_id=gasto.id,
                    monto=gasto.monto,
                )

                # Invalidate cache on write
                self.cache_service.invalidate("gastos*")

                return ServiceResult(value=gasto, status_code=201)
        except Exception as e:
            self.logger.error(
                "Error al crear gasto",
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

    async def get_by_id(self, gasto_id: int) -> ServiceResult:
        cache_key = f"gasto:{gasto_id}"

        # Try cache first
        cached = self.cache_service.get(cache_key)
        if cached:
            return ServiceResult(value=cached)

        async with self.uow as uow:
            gasto = await uow.expense_repo.get_by_id_with_category(gasto_id)
            if not gasto:
                return ServiceResult(
                    error="Gasto no encontrado", status_code=404
                )

            # Store in cache
            self.cache_service.set(cache_key, gasto)
            return ServiceResult(value=gasto)

    async def list_all(self) -> ServiceResult:
        cache_key = "gastos:all"

        # Try cache first
        cached = self.cache_service.get(cache_key)
        if cached:
            return ServiceResult(value=cached)

        async with self.uow as uow:
            gastos = await uow.expense_repo.list()

            # Store in cache
            self.cache_service.set(cache_key, gastos)
            return ServiceResult(value=gastos)

    async def list_by_filters(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        categoria_gasto_id: Optional[int] = None,
    ) -> ServiceResult:
        # Generate cache key based on filters
        cache_key = f"gastos:filters:{hash(str((fecha_desde, fecha_hasta, categoria_gasto_id)))}"

        # Try cache first
        cached = self.cache_service.get(cache_key)
        if cached:
            return ServiceResult(value=cached)

        async with self.uow as uow:
            gastos = await uow.expense_repo.list_by_filters(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                categoria_gasto_id=categoria_gasto_id,
            )

            # Store in cache
            self.cache_service.set(cache_key, gastos)
            return ServiceResult(value=gastos)

    async def update(
        self,
        gasto_id: int,
        gasto_update: GastoUpdateRequest,
        username: str,
    ) -> ServiceResult:
        try:
            async with self.uow as uow:
                gasto = await uow.expense_repo.get_by_id(gasto_id)
                if not gasto:
                    return ServiceResult(
                        error="Gasto no encontrado", status_code=404
                    )

                # Capturar estado anterior para auditoría
                old_gasto_dict = {
                    "id": gasto.id,
                    "categoria_gasto_id": gasto.categoria_gasto_id,
                    "descripcion": gasto.descripcion,
                    "monto": gasto.monto,
                    "fecha_pago": gasto.fecha_pago,
                    "activo": gasto.activo,
                }

                # Validar nueva categoría si se actualiza
                if (
                    gasto_update.categoria_gasto_id is not None
                    and gasto_update.categoria_gasto_id != gasto.categoria_gasto_id
                ):
                    categoria = await uow.expense_category_repo.get_by_id(
                        gasto_update.categoria_gasto_id
                    )
                    if not categoria:
                        return ServiceResult(
                            error="Categoría de gasto no encontrada", status_code=404
                        )

                for var, value in vars(gasto_update).items():
                    if value is not None:
                        setattr(gasto, var, value)

                gasto.fecha_actualizacion = datetime.now()
                await uow.commit()
                await uow.expense_repo.refresh(gasto)

                # Auditar actualización
                if self.audit_service:
                    old_gast = Expense(**old_gasto_dict)
                    await self.audit_service.log_update(
                        username=username,
                        entity_type="Expense",
                        old_entity=old_gast,
                        new_entity=gasto,
                    )

                # Invalidate cache on write
                self.cache_service.invalidate("gastos*")

                return ServiceResult(value=gasto)
        except Exception as e:
            self.logger.error(
                "Error al actualizar gasto",
                error=str(e),
                gasto_id=gasto_id,
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

    async def delete(
        self,
        gasto_id: int,
        username: str,
    ) -> ServiceResult:
        try:
            async with self.uow as uow:
                gasto = await uow.expense_repo.get_by_id(gasto_id)
                if not gasto:
                    return ServiceResult(
                        error="Gasto no encontrado", status_code=404
                    )

                # Soft delete
                gasto.activo = False
                gasto.fecha_actualizacion = datetime.now()
                await uow.commit()

                # Auditar eliminación
                if self.audit_service:
                    await self.audit_service.log_deletion(
                        username=username,
                        entity_type="Expense",
                        entity=gasto,
                    )

                # Invalidate cache on write
                self.cache_service.invalidate("gastos*")

                self.logger.debug(
                    "Gasto eliminado (soft delete)",
                    gasto_id=gasto_id,
                )

                return ServiceResult(value=gasto, status_code=204)
        except Exception as e:
            self.logger.error(
                "Error al eliminar gasto",
                error=str(e),
                gasto_id=gasto_id,
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

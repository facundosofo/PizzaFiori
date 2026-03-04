from dataclasses import dataclass
from typing import Any, Optional, List
from datetime import datetime
import structlog

from app.domain.models.category_stock import CategoryStock
from app.domain.unit_of_work import AbstractUnitOfWork


@dataclass
class ServiceResult:
    value: Optional[Any] = None
    error: Optional[str] = None
    status_code: int = 200


def _compute_estado(
    cantidad: int,
    umbral_amarillo: Optional[int],
    umbral_rojo: Optional[int],
) -> str:
    if cantidad == 0:
        return "sin_stock"
    if umbral_rojo is not None and cantidad <= umbral_rojo:
        return "critical"
    if umbral_amarillo is not None and cantidad <= umbral_amarillo:
        return "warning"
    return "ok"


class StockService:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        logger: structlog.BoundLogger | None = None,
    ):
        self.uow = uow
        self.logger = logger or structlog.get_logger(__name__)

    async def get_all_stocks(self) -> ServiceResult:
        """Devuelve el stock actual de todas las categorías activas."""
        try:
            async with self.uow as uow:
                categorias = await uow.product_category_repo.list_by_active(True)
                stocks = await uow.stock_repo.get_all()

            stocks_by_cat = {s.categoria_id: s for s in stocks}

            result = []
            for cat in sorted(categorias, key=lambda c: c.id):
                stock = stocks_by_cat.get(cat.id)
                cantidad = stock.cantidad if stock else 0
                umbral_amarillo = stock.umbral_amarillo if stock else None
                umbral_rojo = stock.umbral_rojo if stock else None
                estado = _compute_estado(cantidad, umbral_amarillo, umbral_rojo)
                result.append(
                    {
                        "categoria_id": cat.id,
                        "categoria_nombre": cat.nombre,
                        "cantidad": cantidad,
                        "umbral_amarillo": umbral_amarillo,
                        "umbral_rojo": umbral_rojo,
                        "estado": estado,
                    }
                )

            return ServiceResult(value=result)

        except Exception as e:
            self.logger.error("Error al obtener stock", error=str(e), exc_info=True)
            return ServiceResult(error=str(e), status_code=500)

    async def add_stock(
        self,
        categoria_id: int,
        cantidad: int,
        username: str,
    ) -> ServiceResult:
        """Ajusta el stock de una categoría (positivo = agregar, negativo = quitar) y deja registro de auditoría."""
        try:
            if cantidad == 0:
                return ServiceResult(
                    error="La cantidad no puede ser cero", status_code=400
                )

            async with self.uow as uow:
                cat = await uow.product_category_repo.get_by_id(categoria_id)
                if not cat:
                    return ServiceResult(
                        error="Categoría no encontrada", status_code=404
                    )

                stock = await uow.stock_repo.get_by_categoria_id(categoria_id)
                if stock is None:
                    stock = CategoryStock(
                        categoria_id=categoria_id,
                        cantidad=0,
                        fecha_actualizacion=datetime.now(),
                    )
                    await uow.stock_repo.upsert(stock)

                stock_anterior = stock.cantidad
                stock.cantidad = max(0, stock.cantidad + cantidad)
                stock.fecha_actualizacion = datetime.now()

                tipo_movimiento = "INGRESO" if cantidad > 0 else "AJUSTE_BAJA"
                await uow.audit_repo.log_action(
                    username=username,
                    entity_type="Stock",
                    entity_id=categoria_id,
                    action="UPDATE",
                    changes={
                        "tipo": tipo_movimiento,
                        "cantidad": cantidad,
                        "stock_anterior": stock_anterior,
                        "stock_nuevo": stock.cantidad,
                        "categoria_nombre": cat.nombre,
                    },
                )
                await uow.commit()

                _cantidad = stock.cantidad
                _umbral_amarillo = stock.umbral_amarillo
                _umbral_rojo = stock.umbral_rojo
                _cat_nombre = cat.nombre

            estado = _compute_estado(_cantidad, _umbral_amarillo, _umbral_rojo)
            return ServiceResult(
                value={
                    "categoria_id": categoria_id,
                    "categoria_nombre": _cat_nombre,
                    "cantidad": _cantidad,
                    "umbral_amarillo": _umbral_amarillo,
                    "umbral_rojo": _umbral_rojo,
                    "estado": estado,
                },
                status_code=200,
            )

        except Exception as e:
            self.logger.error("Error al agregar stock", error=str(e), exc_info=True)
            return ServiceResult(error=str(e), status_code=500)

    async def configure_alerts(
        self,
        categoria_id: int,
        umbral_amarillo: Optional[int],
        umbral_rojo: Optional[int],
        username: str,
    ) -> ServiceResult:
        """Configura los umbrales de stock para una categoría."""
        try:
            async with self.uow as uow:
                cat = await uow.product_category_repo.get_by_id(categoria_id)
                if not cat:
                    return ServiceResult(
                        error="Categoría no encontrada", status_code=404
                    )

                stock = await uow.stock_repo.get_by_categoria_id(categoria_id)
                if stock is None:
                    stock = CategoryStock(
                        categoria_id=categoria_id,
                        cantidad=0,
                        fecha_actualizacion=datetime.now(),
                    )
                    await uow.stock_repo.upsert(stock)

                stock.umbral_amarillo = umbral_amarillo
                stock.umbral_rojo = umbral_rojo
                stock.fecha_actualizacion = datetime.now()

                await uow.audit_repo.log_action(
                    username=username,
                    entity_type="Stock",
                    entity_id=categoria_id,
                    action="UPDATE",
                    changes={
                        "tipo": "CONFIG_ALERTAS",
                        "umbral_amarillo": umbral_amarillo,
                        "umbral_rojo": umbral_rojo,
                        "categoria_nombre": cat.nombre,
                    },
                )
                await uow.commit()

                _cantidad = stock.cantidad
                _umbral_amarillo = stock.umbral_amarillo
                _umbral_rojo = stock.umbral_rojo
                _cat_nombre = cat.nombre

            estado = _compute_estado(_cantidad, _umbral_amarillo, _umbral_rojo)
            return ServiceResult(
                value={
                    "categoria_id": categoria_id,
                    "categoria_nombre": _cat_nombre,
                    "cantidad": _cantidad,
                    "umbral_amarillo": _umbral_amarillo,
                    "umbral_rojo": _umbral_rojo,
                    "estado": estado,
                }
            )

        except Exception as e:
            self.logger.error(
                "Error al configurar umbrales de stock", error=str(e), exc_info=True
            )
            return ServiceResult(error=str(e), status_code=500)

    async def get_movements(
        self, categoria_id: int, limit: int = 50
    ) -> ServiceResult:
        """Devuelve el historial de movimientos de stock para una categoría."""
        try:
            async with self.uow as uow:
                movements = await uow.audit_repo.get_by_entity(
                    entity_type="Stock",
                    entity_id=categoria_id,
                    limit=limit,
                )

            result = [
                {
                    "id": m.id,
                    "timestamp": m.timestamp,
                    "username": m.username,
                    "action": m.action,
                    "changes": m.changes,
                }
                for m in movements
            ]
            return ServiceResult(value=result)

        except Exception as e:
            self.logger.error(
                "Error al obtener movimientos de stock", error=str(e), exc_info=True
            )
            return ServiceResult(error=str(e), status_code=500)

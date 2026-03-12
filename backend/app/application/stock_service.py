from dataclasses import dataclass
from typing import Any, Optional, List
from datetime import datetime
import structlog

from app.domain.models.category_stock import CategoryStock
from app.domain.models.product_stock import ProductStock
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
        """Devuelve el stock actual de todas las categorías activas con sus flags de configuración."""
        try:
            async with self.uow as uow:
                categorias = await uow.product_category_repo.list_by_active(True)
                stocks = await uow.stock_repo.get_all()

            stocks_by_cat = {s.categoria_id: s for s in stocks}

            result = []

            for cat in sorted(categorias, key=lambda c: c.id):
                stock = stocks_by_cat.get(cat.id)
                umbral_amarillo = stock.umbral_amarillo if stock else None
                umbral_rojo = stock.umbral_rojo if stock else None

                if cat.stock_por_producto:
                    async with self.uow as uow2:
                        producto_stocks = await uow2.product_stock_repo.get_by_categoria_id(cat.id)
                    cantidad = sum(ps.cantidad for ps in producto_stocks)
                    num_productos = len(producto_stocks)
                else:
                    cantidad = stock.cantidad if stock else 0
                    num_productos = None

                estado = _compute_estado(cantidad, umbral_amarillo, umbral_rojo)

                result.append(
                    {
                        "categoria_id": cat.id,
                        "categoria_nombre": cat.nombre,
                        "cantidad": cantidad,
                        "umbral_amarillo": umbral_amarillo,
                        "umbral_rojo": umbral_rojo,
                        "estado": estado,
                        "stock_visible": cat.stock_visible,
                        "stock_por_producto": cat.stock_por_producto,
                        "num_productos": num_productos,
                    }
                )

            return ServiceResult(
                value={
                    "categorias": [entry for entry in result if entry["stock_visible"]],
                }
            )

        except Exception as e:
            self.logger.error("Error al obtener stock", error=str(e), exc_info=True)
            return ServiceResult(error=str(e), status_code=500)

    async def get_stock_config(self) -> ServiceResult:
        """Devuelve la configuración de stock (flags) para todas las categorías activas."""
        try:
            async with self.uow as uow:
                categorias = await uow.product_category_repo.list_by_active(True)

            result = [
                {
                    "categoria_id": cat.id,
                    "categoria_nombre": cat.nombre,
                    "stock_visible": cat.stock_visible,
                    "stock_por_producto": cat.stock_por_producto,
                }
                for cat in sorted(categorias, key=lambda c: c.id)
            ]
            return ServiceResult(value=result)

        except Exception as e:
            self.logger.error("Error al obtener config de stock", error=str(e), exc_info=True)
            return ServiceResult(error=str(e), status_code=500)

    async def save_stock_config(self, configs: list, username: str) -> ServiceResult:
        """Guarda la configuración de visibilidad y desglose por producto para cada categoría."""
        try:
            async with self.uow as uow:
                for cfg in configs:
                    cat = await uow.product_category_repo.get_by_id(cfg["categoria_id"])
                    if not cat:
                        continue

                    enabling_per_product = cfg["stock_por_producto"] and not cat.stock_por_producto

                    cat.stock_visible = cfg["stock_visible"]
                    cat.stock_por_producto = cfg["stock_por_producto"]
                    cat.fecha_actualizacion = datetime.now()

                    if enabling_per_product:
                        productos = await uow.product_repo.list(categoria_id=cat.id, active=True)
                        for producto in productos:
                            await uow.product_stock_repo.get_or_create(producto.id)

                    await uow.audit_repo.log_action(
                        username=username,
                        entity_type="StockConfig",
                        entity_id=cat.id,
                        action="UPDATE",
                        changes={
                            "tipo": "CONFIG_STOCK",
                            "stock_visible": cfg["stock_visible"],
                            "stock_por_producto": cfg["stock_por_producto"],
                            "categoria_nombre": cat.nombre,
                        },
                    )

                await uow.commit()

            return ServiceResult(value={"ok": True})

        except Exception as e:
            self.logger.error("Error al guardar config de stock", error=str(e), exc_info=True)
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

                if cat.stock_por_producto:
                    return ServiceResult(
                        error="Esta categoría usa stock por producto. Modificá el stock de cada producto individualmente.",
                        status_code=400,
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
                _stock_visible = cat.stock_visible
                _stock_por_producto = cat.stock_por_producto

            estado = _compute_estado(_cantidad, _umbral_amarillo, _umbral_rojo)
            return ServiceResult(
                value={
                    "categoria_id": categoria_id,
                    "categoria_nombre": _cat_nombre,
                    "cantidad": _cantidad,
                    "umbral_amarillo": _umbral_amarillo,
                    "umbral_rojo": _umbral_rojo,
                    "estado": estado,
                    "stock_visible": _stock_visible,
                    "stock_por_producto": _stock_por_producto,
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
                _stock_visible = cat.stock_visible
                _stock_por_producto = cat.stock_por_producto

            estado = _compute_estado(_cantidad, _umbral_amarillo, _umbral_rojo)
            return ServiceResult(
                value={
                    "categoria_id": categoria_id,
                    "categoria_nombre": _cat_nombre,
                    "cantidad": _cantidad,
                    "umbral_amarillo": _umbral_amarillo,
                    "umbral_rojo": _umbral_rojo,
                    "estado": estado,
                    "stock_visible": _stock_visible,
                    "stock_por_producto": _stock_por_producto,
                }
            )

        except Exception as e:
            self.logger.error(
                "Error al configurar umbrales de stock", error=str(e), exc_info=True
            )
            return ServiceResult(error=str(e), status_code=500)

    async def get_product_stocks(self, categoria_id: int) -> ServiceResult:
        """Devuelve el desglose de stock por producto para una categoría."""
        try:
            async with self.uow as uow:
                cat = await uow.product_category_repo.get_by_id(categoria_id)
                if not cat:
                    return ServiceResult(error="Categoría no encontrada", status_code=404)

                if not cat.stock_por_producto:
                    return ServiceResult(
                        error="Esta categoría no tiene stock por producto habilitado",
                        status_code=400,
                    )

                # Ensure all active products have a stock entry
                productos = await uow.product_repo.list(categoria_id=categoria_id, active=True)
                for p in productos:
                    await uow.product_stock_repo.get_or_create(p.id)
                await uow.commit()

                producto_stocks = await uow.product_stock_repo.get_by_categoria_id(categoria_id)

            result = []
            for ps in producto_stocks:
                estado = _compute_estado(ps.cantidad, ps.umbral_amarillo, ps.umbral_rojo)
                result.append({
                    "producto_id": ps.producto_id,
                    "producto_nombre": ps.producto.nombre if ps.producto else f"Producto {ps.producto_id}",
                    "cantidad": ps.cantidad,
                    "umbral_amarillo": ps.umbral_amarillo,
                    "umbral_rojo": ps.umbral_rojo,
                    "estado": estado,
                })

            result.sort(key=lambda item: item["producto_id"])
            return ServiceResult(value=result)

        except Exception as e:
            self.logger.error("Error al obtener stock por producto", error=str(e), exc_info=True)
            return ServiceResult(error=str(e), status_code=500)

    async def add_product_stock(
        self,
        producto_id: int,
        cantidad: int,
        username: str,
    ) -> ServiceResult:
        """Ajusta el stock de un producto individual."""
        try:
            if cantidad == 0:
                return ServiceResult(error="La cantidad no puede ser cero", status_code=400)

            async with self.uow as uow:
                producto = await uow.product_repo.get_by_id(producto_id)
                if not producto:
                    return ServiceResult(error="Producto no encontrado", status_code=404)

                stock = await uow.product_stock_repo.get_or_create(producto_id)
                stock_anterior = stock.cantidad
                stock.cantidad = max(0, stock.cantidad + cantidad)
                stock.fecha_actualizacion = datetime.now()

                tipo_movimiento = "INGRESO" if cantidad > 0 else "AJUSTE_BAJA"
                await uow.audit_repo.log_action(
                    username=username,
                    entity_type="StockProducto",
                    entity_id=producto_id,
                    action="UPDATE",
                    changes={
                        "tipo": tipo_movimiento,
                        "cantidad": cantidad,
                        "stock_anterior": stock_anterior,
                        "stock_nuevo": stock.cantidad,
                        "producto_nombre": producto.nombre,
                    },
                )
                await uow.commit()

                _cantidad = stock.cantidad
                _umbral_amarillo = stock.umbral_amarillo
                _umbral_rojo = stock.umbral_rojo
                _nombre = producto.nombre

            estado = _compute_estado(_cantidad, _umbral_amarillo, _umbral_rojo)
            return ServiceResult(
                value={
                    "producto_id": producto_id,
                    "producto_nombre": _nombre,
                    "cantidad": _cantidad,
                    "umbral_amarillo": _umbral_amarillo,
                    "umbral_rojo": _umbral_rojo,
                    "estado": estado,
                }
            )

        except Exception as e:
            self.logger.error("Error al agregar stock de producto", error=str(e), exc_info=True)
            return ServiceResult(error=str(e), status_code=500)

    async def configure_product_alerts(
        self,
        producto_id: int,
        umbral_amarillo: Optional[int],
        umbral_rojo: Optional[int],
        username: str,
    ) -> ServiceResult:
        """Configura los umbrales de alerta para un producto individual."""
        try:
            async with self.uow as uow:
                producto = await uow.product_repo.get_by_id(producto_id)
                if not producto:
                    return ServiceResult(error="Producto no encontrado", status_code=404)

                stock = await uow.product_stock_repo.get_or_create(producto_id)
                stock.umbral_amarillo = umbral_amarillo
                stock.umbral_rojo = umbral_rojo
                stock.fecha_actualizacion = datetime.now()

                await uow.audit_repo.log_action(
                    username=username,
                    entity_type="StockProducto",
                    entity_id=producto_id,
                    action="UPDATE",
                    changes={
                        "tipo": "CONFIG_ALERTAS",
                        "umbral_amarillo": umbral_amarillo,
                        "umbral_rojo": umbral_rojo,
                        "producto_nombre": producto.nombre,
                    },
                )
                await uow.commit()

                _cantidad = stock.cantidad
                _umbral_amarillo = stock.umbral_amarillo
                _umbral_rojo = stock.umbral_rojo
                _nombre = producto.nombre

            estado = _compute_estado(_cantidad, _umbral_amarillo, _umbral_rojo)
            return ServiceResult(
                value={
                    "producto_id": producto_id,
                    "producto_nombre": _nombre,
                    "cantidad": _cantidad,
                    "umbral_amarillo": _umbral_amarillo,
                    "umbral_rojo": _umbral_rojo,
                    "estado": estado,
                }
            )

        except Exception as e:
            self.logger.error("Error al configurar alertas de producto", error=str(e), exc_info=True)
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

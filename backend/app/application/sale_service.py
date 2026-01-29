from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import structlog

from app.domain.models.sale import Sale
from app.domain.models.sale_item import SaleItem
from app.domain.unit_of_work import AbstractUnitOfWork
from app.presentation.schemas.sale_schemas import SaleCreateRequest


@dataclass
class ServiceResult:
    value: Optional[Sale | List[Sale]] = None
    error: Optional[str] = None
    status_code: int = 200


class SaleService:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        logger: structlog.BoundLogger | None = None,
    ):
        self.uow = uow
        self.logger = logger or structlog.get_logger(__name__)

    def _get_product_price(self, producto, cantidad: int) -> Optional[Decimal]:
        """
        Calcula el precio total usando sistema de rangos.
        
        Ejemplo: Si compras 7 empanadas con precios:
        - 1 unidad: $1200
        - 6 unidades: $6000
        - 12 unidades: $10800
        
        Cálculo para 7:
        - Primeras 6 al precio de 6: $6000
        - La 7ma al precio de 1: $1200
        - Total: $7200
        
        Retorna el precio TOTAL (no unitario), que luego se divide por la cantidad
        para obtener el precio_unitario en la venta.
        """
        if not producto or not producto.activo:
            return None
        
        if not producto.precios:
            return None
        
        # Ordenar precios por cantidad descendente
        precios_ordenados = sorted(producto.precios, key=lambda p: p.cantidad, reverse=True)
        
        cantidad_restante = cantidad
        precio_total = Decimal("0.00")
        
        # Aplicar rangos de mayor a menor
        for rango_precio in precios_ordenados:
            if cantidad_restante >= rango_precio.cantidad:
                # Cuántas veces entra este rango completo
                veces = cantidad_restante // rango_precio.cantidad
                precio_total += rango_precio.precio * veces
                cantidad_restante = cantidad_restante % rango_precio.cantidad
                
                if cantidad_restante == 0:
                    break
        
        # Si quedan unidades, aplicar el precio del rango más pequeño
        if cantidad_restante > 0:
            precio_minimo = min(precios_ordenados, key=lambda p: p.cantidad)
            # Calcular precio unitario del rango más pequeño
            precio_unitario_minimo = precio_minimo.precio / precio_minimo.cantidad
            precio_total += precio_unitario_minimo * cantidad_restante
        
        # Retornar precio unitario promedio (para mantener compatibilidad con el resto del código)
        return precio_total / cantidad

    def _get_offer_price(self, oferta) -> Optional[Decimal]:
        """Obtiene el precio de una oferta."""
        if not oferta or not oferta.activo:
            return None
        
        return oferta.precio

    async def create(self, sale_create: SaleCreateRequest) -> ServiceResult:
        """Crea una nueva venta."""
        try:
            self.logger.debug(
                "Creando venta",
                numero_orden=sale_create.numero_orden,
                items_count=len(sale_create.items),
            )

            sale_items = []
            total = Decimal("0.00")

            async with self.uow as uow:
                # Validar y calcular precios para cada item
                for item in sale_create.items:
                    precio_unitario = None
                    
                    if item.producto_id:
                        # Validar que el producto existe y está activo
                        producto = await uow.product_repo.get_by_id(item.producto_id)
                        if not producto:
                            return ServiceResult(
                                error=f"Producto {item.producto_id} no encontrado",
                                status_code=404,
                            )
                        
                        # Obtener precio según cantidad
                        precio_unitario = self._get_product_price(producto, item.cantidad)
                        if precio_unitario is None:
                            return ServiceResult(
                                error=f"No se pudo obtener el precio para el producto {item.producto_id} con cantidad {item.cantidad}",
                                status_code=400,
                            )
                    
                    elif item.oferta_id:
                        # Validar que la oferta existe y está activa
                        oferta = await uow.offer_repo.get_by_id(item.oferta_id)
                        if not oferta:
                            return ServiceResult(
                                error=f"Oferta {item.oferta_id} no encontrada",
                                status_code=404,
                            )
                        
                        # Obtener precio de la oferta
                        precio_unitario = self._get_offer_price(oferta)
                        if precio_unitario is None:
                            return ServiceResult(
                                error=f"No se pudo obtener el precio para la oferta {item.oferta_id}",
                                status_code=400,
                            )
                    
                    # Calcular subtotal
                    subtotal = Decimal(str(precio_unitario)) * Decimal(str(item.cantidad))
                    total += subtotal
                    
                    sale_item = SaleItem(
                        producto_id=item.producto_id,
                        oferta_id=item.oferta_id,
                        cantidad=item.cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal,
                    )
                    sale_items.append(sale_item)

                sale = Sale(
                    numero_orden=sale_create.numero_orden,
                    total=total,
                    fecha_creacion=datetime.now(),
                    fecha_actualizacion=datetime.now(),
                    items=sale_items,
                )

                await uow.sale_repo.add(sale)
                await uow.commit()
                await uow.sale_repo.refresh(sale, attribute_names=["items"])

            self.logger.info(
                "Venta creada exitosamente",
                sale_id=sale.id,
                total=float(sale.total),
                items_count=len(sale.items),
            )

            return ServiceResult(value=sale, status_code=201)

        except Exception as e:
            self.logger.error(
                "Error al crear venta",
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

    async def get_by_id(self, sale_id: int) -> ServiceResult:
        """Obtiene una venta por ID."""
        try:
            async with self.uow as uow:
                sale = await uow.sale_repo.get_by_id(sale_id)

            if not sale:
                return ServiceResult(
                    error=f"Venta {sale_id} no encontrada",
                    status_code=404,
                )

            return ServiceResult(value=sale)

        except Exception as e:
            self.logger.error(
                "Error al obtener venta",
                sale_id=sale_id,
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=500)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Sale]:
        try:
            async with self.uow as uow:
                return await uow.sale_repo.list(skip=skip, limit=limit)
        except Exception as e:
            self.logger.error(
                "Error al listar ventas",
                error=str(e),
                exc_info=True,
            )
            return []

    async def count_all(self) -> int:
        """Cuenta el total de ventas en la base de datos."""
        try:
            async with self.uow as uow:
                return await uow.sale_repo.count()
        except Exception as e:
            self.logger.error(
                "Error al contar ventas",
                error=str(e),
                exc_info=True,
            )
            return 0

    async def update(self, sale_id: int, sale_update) -> ServiceResult:
        """Actualiza una venta existente."""
        try:
            self.logger.debug(
                "Actualizando venta",
                sale_id=sale_id,
                numero_orden=sale_update.numero_orden,
                items_count=len(sale_update.items),
            )

            async with self.uow as uow:
                # Verificar que la venta existe
                existing_sale = await uow.sale_repo.get_by_id(sale_id)
                if not existing_sale:
                    return ServiceResult(
                        error=f"Venta {sale_id} no encontrada",
                        status_code=404,
                    )

                # Calcular nuevos items y total
                sale_items = []
                total = Decimal("0.00")

                for item in sale_update.items:
                    # Usar precio_unitario recibido, validar que exista
                    if item.precio_unitario is None:
                        return ServiceResult(
                            error="Se debe proporcionar precio_unitario para cada item en la actualización",
                            status_code=400,
                        )
                    
                    precio_unitario = item.precio_unitario
                    
                    # Validar que el producto o oferta existe
                    if item.producto_id:
                        producto = await uow.product_repo.get_by_id(item.producto_id)
                        if not producto:
                            return ServiceResult(
                                error=f"Producto {item.producto_id} no encontrado",
                                status_code=404,
                            )
                    elif item.oferta_id:
                        oferta = await uow.offer_repo.get_by_id(item.oferta_id)
                        if not oferta:
                            return ServiceResult(
                                error=f"Oferta {item.oferta_id} no encontrada",
                                status_code=404,
                            )
                    
                    subtotal = Decimal(str(precio_unitario)) * Decimal(str(item.cantidad))
                    total += subtotal
                    
                    sale_item = SaleItem(
                        producto_id=item.producto_id,
                        oferta_id=item.oferta_id,
                        cantidad=item.cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal,
                    )
                    sale_items.append(sale_item)

                # Actualizar venta
                existing_sale.numero_orden = sale_update.numero_orden
                existing_sale.total = total
                existing_sale.fecha_actualizacion = datetime.now()
                existing_sale.items = sale_items

                await uow.sale_repo.update(existing_sale)
                await uow.commit()
                await uow.sale_repo.refresh(existing_sale, attribute_names=["items"])

            self.logger.info(
                "Venta actualizada exitosamente",
                sale_id=sale_id,
                total=float(existing_sale.total),
                items_count=len(existing_sale.items),
            )

            return ServiceResult(value=existing_sale)

        except Exception as e:
            self.logger.error(
                "Error al actualizar venta",
                sale_id=sale_id,
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

    async def delete(self, sale_id: int) -> ServiceResult:
        """Elimina una venta."""
        try:
            self.logger.debug("Eliminando venta", sale_id=sale_id)

            async with self.uow as uow:
                sale = await uow.sale_repo.get_by_id(sale_id)
                
                if not sale:
                    return ServiceResult(
                        error=f"Venta {sale_id} no encontrada",
                        status_code=404,
                    )

                await uow.sale_repo.delete(sale)
                await uow.commit()

            self.logger.info("Venta eliminada exitosamente", sale_id=sale_id)

            return ServiceResult(status_code=204)

        except Exception as e:
            self.logger.error(
                "Error al eliminar venta",
                sale_id=sale_id,
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

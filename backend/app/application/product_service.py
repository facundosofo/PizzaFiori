from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal, ROUND_HALF_UP
from fastapi import UploadFile
from datetime import datetime
import structlog
from app.domain.models.product import Product
from app.domain.models.product_price import ProductPrice
from app.domain.unit_of_work import AbstractUnitOfWork
from app.presentation.schemas.product_schemas import ProductoCreateRequest, ProductoUpdateRequest
from app.infrastructure.file_service import FileService
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.sku_generator import generar_sku_producto


@dataclass
class ServiceResult:
    value: Optional[Product] = None
    error: Optional[str] = None
    status_code: int = 200


class ProductService:
    def __init__(
        self, 
        uow: AbstractUnitOfWork, 
        file_service: FileService,
        cache_service: CacheService,
        audit_service=None,  # Optional for backward compatibility
        logger: structlog.BoundLogger | None = None
    ):
        self.uow = uow
        self.file_service = file_service
        self.cache_service = cache_service
        self.audit_service = audit_service
        self.logger = logger or structlog.get_logger(__name__)


    async def create(
        self,
        producto_create: ProductoCreateRequest,
        image: Optional[UploadFile] = None,
        username: Optional[str] = None
    ) -> ServiceResult:

        ruta_imagen = None

        try:
            self.logger.debug(
                "Creando producto",
                producto_nombre=producto_create.nombre,
                categoria_id=producto_create.categoria_id,
                tiene_imagen=image is not None
            )
            
            async with self.uow as uow:
                # Validar que la categoría existe y generar SKU antes de guardar la imagen
                categoria_nombre = None
                if producto_create.categoria_id:
                    categoria = await uow.product_category_repo.get_by_id(producto_create.categoria_id)
                    if not categoria:
                        return ServiceResult(error="Categoría no encontrada", status_code=404)
                    categoria_nombre = categoria.nombre

                sku = generar_sku_producto(producto_create.nombre, categoria_nombre)

            if image:
                ruta_imagen = await self.file_service.save_file(image, filename_base=sku)
                self.logger.debug("Imagen guardada", ruta=ruta_imagen)

            async with self.uow as uow:
                producto = Product(
                    sku=sku,
                    nombre=producto_create.nombre,
                    categoria_id=producto_create.categoria_id,
                    imagen=ruta_imagen,
                    activo=True,
                    fecha_creacion=datetime.now(),
                    fecha_actualizacion=datetime.now(),
                    precios=[
                        ProductPrice(
                            cantidad=precio.cantidad,
                            precio=precio.precio
                        )
                        for precio in producto_create.precios
                    ],
                )

                await uow.product_repo.add(producto)
                await uow.commit()
                producto = await uow.product_repo.get_by_id(producto.id)

            # Auditar creación (usa su propia transacción)
            if self.audit_service and username:
                await self.audit_service.log_creation(
                    username=username,
                    entity_type="Product",
                    entity=producto,
                )

            self.logger.info(
                "Producto creado exitosamente",
                producto_id=producto.id,
                producto_nombre=producto.nombre
            )
            
            # Invalidate product cache on write (selective)
            self.cache_service.invalidate('producto_*')
            
            return ServiceResult(value=producto, status_code=201)

        except Exception as e:
            self.logger.error(
                "Error al crear producto",
                error=str(e),
                producto_nombre=producto_create.nombre,
                exc_info=True
            )
            
            if ruta_imagen:
                self.file_service.delete_file(ruta_imagen)

            return ServiceResult(error=str(e), status_code=400)


    async def get_all(
        self,
        categoria_id: Optional[int] = None,
        active: Optional[bool] = None
    ) -> List[Product]:

        async with self.uow as uow:
            return await uow.product_repo.list(
                categoria_id=categoria_id,
                active=active,
            )

    

    async def get_by_id(self, producto_id: int) -> ServiceResult:
        async with self.uow as uow:
            producto = await uow.product_repo.get_by_id(producto_id)

            if not producto:
                return ServiceResult(error="Producto no encontrado", status_code=404)

            return ServiceResult(value=producto)


    async def update(
        self,
        producto_id: int,
        producto_update: Optional[ProductoUpdateRequest] = None,
        image: Optional[UploadFile] = None,
        active: Optional[bool] = None,
        username: Optional[str] = None,
        is_logical_delete: bool = False,
    ) -> ServiceResult:

        ruta_imagen_nueva = None

        try:
            async with self.uow as uow:
                producto = await uow.product_repo.get_by_id(producto_id)

                if not producto:
                    return ServiceResult(error="Producto no encontrado", status_code=404)

                # Capturar estado anterior completo para auditoría (incluyendo precios)
                from copy import deepcopy
                old_producto_snapshot = {
                    'id': producto.id,
                    'sku': producto.sku,
                    'nombre': producto.nombre,
                    'categoria_id': producto.categoria_id,
                    'imagen': producto.imagen,
                    'activo': producto.activo,
                    'fecha_creacion': producto.fecha_creacion.isoformat() if producto.fecha_creacion else None,
                    'fecha_actualizacion': producto.fecha_actualizacion.isoformat() if producto.fecha_actualizacion else None,
                    'precios': [
                        {
                            'cantidad': p.cantidad,
                            'precio': float(p.precio) if p.precio else 0.0
                        }
                        for p in (producto.precios or [])
                    ]
                }

                ruta_imagen_vieja = producto.imagen
                sku_producto = producto.sku

                if image:
                    ruta_imagen_nueva = await self.file_service.save_file(image, filename_base=sku_producto)
                    producto.imagen = ruta_imagen_nueva
                
                if producto_update is not None:
                    for var, value in vars(producto_update).items():
                        if value is not None and var != "precios":
                            setattr(producto, var, value)

                    if producto_update.precios is not None:
                        await uow.product_repo.replace_prices(
                                producto.id,
                                [
                                ProductPrice(
                                    producto_id=producto.id,
                                    cantidad=precio.cantidad,
                                    precio=precio.precio,
                                )
                                for precio in producto_update.precios
                            ],
                        )
                        await uow.session.flush()
                        
                if active is not None:
                    producto.activo = active

                producto.fecha_actualizacion = datetime.now()
                await uow.commit()

            # Recargar el producto con las relaciones actualizadas (fuera de la transacción anterior)
            async with self.uow as uow:
                producto = await uow.product_repo.get_by_id(producto_id)
                
                # Capturar nuevo estado para comparación
                new_producto_snapshot = {
                    'id': producto.id,
                    'sku': producto.sku,
                    'nombre': producto.nombre,
                    'categoria_id': producto.categoria_id,
                    'imagen': producto.imagen,
                    'activo': producto.activo,
                    'fecha_creacion': producto.fecha_creacion.isoformat() if producto.fecha_creacion else None,
                    'fecha_actualizacion': producto.fecha_actualizacion.isoformat() if producto.fecha_actualizacion else None,
                    'precios': [
                        {
                            'cantidad': p.cantidad,
                            'precio': float(p.precio) if p.precio else 0.0
                        }
                        for p in (producto.precios or [])
                    ]
                }

            # Auditar actualización con comparación de snapshots
            if self.audit_service and username:
                # Si es eliminación lógica, registrar como DELETE con snapshot completo
                if is_logical_delete:
                    async with self.uow as uow:
                        await uow.audit_repo.log_action(
                            username=username,
                            entity_type="Product",
                            entity_id=producto.id,
                            action="DELETE",
                            changes={"old": old_producto_snapshot},
                        )
                        await uow.commit()
                else:
                    # Calcular diff manualmente para actualizaciones normales
                    diff = {}
                    
                    # Comparar campos simples
                    for key in ['nombre', 'categoria_id', 'imagen', 'activo', 'sku']:
                        old_val = old_producto_snapshot.get(key)
                        new_val = new_producto_snapshot.get(key)
                        if old_val != new_val:
                            diff[key] = {"old": old_val, "new": new_val}
                    
                    # Comparar precios
                    old_precios = old_producto_snapshot.get('precios', [])
                    new_precios = new_producto_snapshot.get('precios', [])
                    if old_precios != new_precios:
                        diff['precios'] = {"old": old_precios, "new": new_precios}
                    
                    # Solo registrar si hay cambios
                    if diff:
                        async with self.uow as uow:
                            await uow.audit_repo.log_action(
                                username=username,
                                entity_type="Product",
                                entity_id=producto.id,
                                action="UPDATE",
                                changes=diff,
                            )
                            await uow.commit()

            if image and ruta_imagen_vieja and ruta_imagen_vieja != ruta_imagen_nueva:
                self.file_service.delete_file(ruta_imagen_vieja)

            # Invalidate product cache on write (selective)
            self.cache_service.invalidate('producto_*')
            
            return ServiceResult(value=producto)

        except Exception as e:
            if ruta_imagen_nueva:
                self.file_service.delete_file(ruta_imagen_nueva)

            return ServiceResult(error=str(e), status_code=400)


    async def bulk_update_prices(
        self,
        monto: Optional[Decimal],
        porcentaje: Optional[Decimal],
        categoria_ids: Optional[List[int]],
        username: Optional[str] = None,
    ) -> ServiceResult:
        """
        Actualiza masivamente los precios de productos activos.
        Aplica monto fijo o porcentaje a todos los precios escalonados.
        Redondea al entero más cercano.
        """
        try:
            self.logger.info(
                "Iniciando actualización masiva de precios",
                monto=str(monto) if monto else None,
                porcentaje=str(porcentaje) if porcentaje else None,
                categoria_ids=categoria_ids,
            )

            # 1. Obtener productos activos (filtrados opcionalmente por categorías)
            async with self.uow as uow:
                productos = await uow.product_repo.list(
                    active=True,
                )

                # Filtrar por categorías en memoria
                if categoria_ids:
                    categoria_ids_set = set(categoria_ids)
                    productos = [
                        p for p in productos if p.categoria_id in categoria_ids_set
                    ]

                if not productos:
                    return ServiceResult(
                        error="No se encontraron productos activos para actualizar",
                        status_code=404,
                    )

                # 2. Capturar snapshots viejos y calcular nuevos precios
                old_snapshots = {}
                updates = {}  # producto_id -> list of new ProductPrice

                for producto in productos:
                    old_snapshots[producto.id] = [
                        {"cantidad": p.cantidad, "precio": float(p.precio)}
                        for p in (producto.precios or [])
                    ]

                    new_prices = []
                    for precio in (producto.precios or []):
                        if monto is not None:
                            nuevo_precio = precio.precio + monto
                        else:
                            nuevo_precio = precio.precio * (1 + porcentaje / Decimal("100"))

                        # Redondear al entero más cercano
                        nuevo_precio = Decimal(str(nuevo_precio)).quantize(
                            Decimal("1"), rounding=ROUND_HALF_UP
                        )

                        if nuevo_precio <= 0:
                            return ServiceResult(
                                error=f"El precio del producto '{producto.nombre}' "
                                      f"(cantidad {precio.cantidad}) resultaría en ${nuevo_precio}, "
                                      f"que no es válido. El precio debe ser mayor a 0.",
                                status_code=400,
                            )

                        new_prices.append(
                            ProductPrice(
                                producto_id=producto.id,
                                cantidad=precio.cantidad,
                                precio=nuevo_precio,
                            )
                        )

                    updates[producto.id] = new_prices

                # 3. Aplicar actualizaciones en una sola transacción
                for producto_id, new_prices in updates.items():
                    await uow.product_repo.replace_prices(producto_id, new_prices)
                await uow.session.flush()

                # Actualizar fecha_actualizacion de cada producto
                for producto in productos:
                    producto.fecha_actualizacion = datetime.now()

                await uow.commit()

            # 4. Recargar productos actualizados en una sola query
            async with self.uow as uow:
                updated_productos = await uow.product_repo.get_by_ids(list(updates.keys()))

            # 5. Auditar cada cambio en una sola transacción
            if self.audit_service and username:
                async with self.uow as uow:
                    for producto in updated_productos:
                        old_precios = old_snapshots.get(producto.id, [])
                        new_precios = [
                            {"cantidad": p.cantidad, "precio": float(p.precio)}
                            for p in (producto.precios or [])
                        ]

                        if old_precios != new_precios:
                            diff = {
                                "precios": {"old": old_precios, "new": new_precios},
                            }
                            await uow.audit_repo.log_action(
                                username=username,
                                entity_type="Product",
                                entity_id=producto.id,
                                action="BULK_UPDATE",
                                changes=diff,
                            )
                    await uow.commit()

            # 6. Invalidar cache
            self.cache_service.invalidate("producto_*")

            self.logger.info(
                "Actualización masiva de precios completada",
                productos_actualizados=len(updated_productos),
            )

            return ServiceResult(
                value={
                    "productos_actualizados": len(updated_productos),
                    "productos": updated_productos,
                }
            )

        except Exception as e:
            self.logger.error(
                "Error en actualización masiva de precios",
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

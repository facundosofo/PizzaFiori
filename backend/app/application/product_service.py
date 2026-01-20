from dataclasses import dataclass
from typing import Optional, List
from fastapi import UploadFile
from datetime import datetime
import structlog
from app.domain.models.product import Product
from app.domain.models.product_price import ProductPrice
from app.domain.unit_of_work import AbstractUnitOfWork
from app.presentation.schemas.product_schemas import ProductoCreateRequest, ProductoUpdateRequest
from app.infrastructure.file_service import FileService


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
        logger: structlog.BoundLogger | None = None
    ):
        self.uow = uow
        self.file_service = file_service
        self.logger = logger or structlog.get_logger(__name__)


    async def create(
        self,
        producto_create: ProductoCreateRequest,
        image: Optional[UploadFile] = None
    ) -> ServiceResult:

        ruta_imagen = None

        try:
            self.logger.debug(
                "Creando producto",
                producto_nombre=producto_create.nombre,
                categoria_id=producto_create.categoria_id,
                tiene_imagen=image is not None
            )
            
            if image:
                ruta_imagen = await self.file_service.save_file(image)
                self.logger.debug("Imagen guardada", ruta=ruta_imagen)

            async with self.uow as uow:
                producto = Product(
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
                await uow.product_repo.refresh(producto, attribute_names=["precios"])

            self.logger.debug(
                "Producto creado exitosamente",
                producto_id=producto.id,
                producto_nombre=producto.nombre
            )
            
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
        active: Optional[bool] = None
    ) -> ServiceResult:

        ruta_imagen_nueva = None

        try:
            async with self.uow as uow:
                producto = await uow.product_repo.get_by_id(producto_id)

                if not producto:
                    return ServiceResult(error="Producto no encontrado", status_code=404)

                ruta_imagen_vieja = producto.imagen

                if image:
                    ruta_imagen_nueva = await self.file_service.save_file(image)
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
                        
                if active is not None:
                    producto.activo = active

                producto.fecha_actualizacion = datetime.now()
                await uow.commit()
                await uow.product_repo.refresh(producto, attribute_names=["precios"])

                if image and ruta_imagen_vieja:
                    self.file_service.delete_file(ruta_imagen_vieja)

                return ServiceResult(value=producto)

        except Exception as e:
            if ruta_imagen_nueva:
                self.file_service.delete_file(ruta_imagen_nueva)

            return ServiceResult(error=str(e), status_code=400)


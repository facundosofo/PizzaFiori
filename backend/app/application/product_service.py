from dataclasses import dataclass
from typing import Optional, List
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime
from app.domain.product import Product
from app.domain.product_price import ProductPrice
from app.presentation.schemas.product_schemas import ProductoCreateRequest, ProductoUpdateRequest
from app.infrastructure.file_service import FileService


@dataclass
class ServiceResult:
    value: Optional[Product] = None
    error: Optional[str] = None
    status_code: int = 200


class ProductService:
    def __init__(self, db: AsyncSession, file_service: FileService):
        self.db = db
        self.file_service = file_service


    async def create(
        self,
        producto_create: ProductoCreateRequest,
        image: Optional[UploadFile] = None
    ) -> ServiceResult:

        ruta_imagen = None

        try:
            if image:
                ruta_imagen = await self.file_service.save_file(image)

            producto = Product(
                nombre=producto_create.nombre,
                categoria_id=producto_create.categoria_id,
                imagen=ruta_imagen,
                activo=True,
                fecha_creacion=datetime.now(),
                fecha_actualizacion=datetime.now()
            )

            self.db.add(producto)
            await self.db.flush()

            if producto_create.precios:
                for precio in producto_create.precios:
                    self.db.add(
                        ProductPrice(
                            producto_id=producto.id,
                            cantidad=precio.cantidad,
                            precio=precio.precio
                        )
                    )

            await self.db.commit()
            await self.db.refresh(producto, attribute_names=["precios"])
            
            return ServiceResult(value=producto, status_code=201)

        except Exception as e:
            await self.db.rollback()

            if ruta_imagen:
                self.file_service.delete_file(ruta_imagen)

            return ServiceResult(error=str(e), status_code=400)


    async def get_all(
        self,
        categoria_id: Optional[int] = None,
        active: Optional[bool] = None
    ) -> List[Product]:

        query = select(Product).options(selectinload(Product.precios))
        
        conditions = []
        if active is not None:
            conditions.append(Product.activo == active)
        if categoria_id is not None:
            conditions.append(Product.categoria_id == categoria_id)

        if conditions:
            query = query.where(*conditions)

        result = await self.db.execute(query)
        return result.scalars().all()

    

    async def get_by_id(self, producto_id: int) -> ServiceResult:
        query = select(Product).where(Product.id == producto_id)
        
        query = query.options(selectinload(Product.precios))

        result = await self.db.execute(query)
        producto = result.scalars().first()

        if not producto:
            return ServiceResult(error="Producto no encontrado", status_code=404)

        return ServiceResult(value=producto)


    async def update(
        self,
        producto_id: int,
        producto_update: ProductoUpdateRequest,
        image: Optional[UploadFile] = None
    ) -> ServiceResult:

        result = await self.db.execute(
            select(Product).where(Product.id == producto_id)
        )
        producto = result.scalars().first()

        if not producto:
            return ServiceResult(error="Producto no encontrado", status_code=404)

        ruta_imagen_vieja = producto.imagen
        ruta_imagen_nueva = None

        try:
            if image:
                ruta_imagen_nueva = await self.file_service.save_file(image)
                producto.imagen = ruta_imagen_nueva

            for var, value in vars(producto_update).items():
                if value is not None and var != "precios":
                    setattr(producto, var, value)

            if producto_update.precios is not None:
                await self.db.execute(
                    ProductPrice.__table__.delete().where(
                        ProductPrice.producto_id == producto.id
                    )
                )

                for precio in producto_update.precios:
                    self.db.add(
                        ProductPrice(
                            producto_id=producto.id,
                            cantidad=precio.cantidad,
                            precio=precio.precio
                        )
                    )

            producto.fecha_actualizacion = datetime.now()

            await self.db.commit()
            await self.db.refresh(producto, attribute_names=["precios"])

            if image and ruta_imagen_vieja:
                self.file_service.delete_file(ruta_imagen_vieja)

            return ServiceResult(value=producto)

        except Exception as e:
            await self.db.rollback()

            if ruta_imagen_nueva:
                self.file_service.delete_file(ruta_imagen_nueva)

            return ServiceResult(error=str(e), status_code=400)


    async def soft_delete(self, producto_id: int) -> ServiceResult:
        result = await self.db.execute(
            select(Product).where(
                Product.id == producto_id,
                Product.activo == True
            )
        )
        producto = result.scalars().first()

        if not producto:
            return ServiceResult(error="Producto no encontrado", status_code=404)

        producto.activo = False
        producto.fecha_actualizacion = datetime.now()

        await self.db.commit()
        return ServiceResult(value=producto)

from dataclasses import dataclass
from typing import Optional, List
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app.domain.products import Producto
from app.presentation.schemas.product_schemas import ProductoCreateRequest, ProductoUpdateRequest
from app.infrastructure.file_service import FileService 

@dataclass
class ServiceResult:
    value: Optional[Producto] = None
    error: Optional[str] = None
    status_code: int = 200

class ProductService:
    def __init__(self, db: AsyncSession, file_service: FileService):
        self.db = db
        self.file_service = file_service

    async def create(self, producto_create: ProductoCreateRequest, image: Optional[UploadFile] = None) -> ServiceResult:
        ruta_imagen = None
        try:
            if image:
                ruta_imagen = await self.file_service.save_file(image)

            producto = Producto(
                nombre=producto_create.nombre,
                descripcion=producto_create.descripcion,
                precio_venta=producto_create.precio_venta,
                categoria_id=producto_create.categoria_id,
                imagen=ruta_imagen,
                activo=True,
                fecha_creacion=datetime.now(),
                fecha_actualizacion=datetime.now()
            )
            
            self.db.add(producto)
            await self.db.commit()
            await self.db.refresh(producto)
            return ServiceResult(value=producto, status_code=201)

        except Exception as e:
            await self.db.rollback()
            if ruta_imagen:
                self.file_service.delete_file(ruta_imagen)
            return ServiceResult(error=str(e), status_code=400)

    async def get_all(self, categoria_id: Optional[int] = None, active: Optional[bool] = None) -> List[Producto]:
        query = select(Producto)
        conditions = []
        if active is not None:
            conditions.append(Producto.activo == active)
        if categoria_id is not None:
            conditions.append(Producto.categoria_id == categoria_id)
        if conditions:
            result = await self.db.execute(query.where(*conditions))
        else:
            result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, producto_id: int) -> ServiceResult:
        result = await self.db.execute(
            select(Producto).where(Producto.id == producto_id)
        )
        producto = result.scalars().first()
        if not producto:
            return ServiceResult(error="Producto no encontrado", status_code=404)
        return ServiceResult(value=producto)

    async def update(self, producto_id: int, producto_update: ProductoUpdateRequest, image: Optional[UploadFile] = None) -> ServiceResult:
        result = await self.db.execute(
            select(Producto).where(Producto.id == producto_id)
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
                if value is not None:
                    setattr(producto, var, value)
            
            producto.fecha_actualizacion = datetime.now()
            await self.db.commit()
            await self.db.refresh(producto)

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
            select(Producto).where(Producto.id == producto_id, Producto.activo == True)
        )
        producto = result.scalars().first()
        if not producto:
            return ServiceResult(error="Producto no encontrado", status_code=404)

        producto.activo = False
        producto.fecha_actualizacion = datetime.now()
        await self.db.commit()
        return ServiceResult(value=producto)

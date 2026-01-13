from dataclasses import dataclass
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.domain.products import Producto
from app.presentation.schemas.product_schemas import ProductoCreateRequest, ProductoUpdateRequest
from datetime import datetime

@dataclass
class ServiceResult:
    value: Optional[Producto] = None
    error: Optional[str] = None
    status_code: int = 200

class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, producto_create: ProductoCreateRequest) -> ServiceResult:
        try:
            producto = Producto(
                nombre=producto_create.nombre,
                descripcion=producto_create.descripcion,
                precio_venta=producto_create.precio_venta,
                activo=True,
                fecha_creacion=datetime.now()
            )
            self.db.add(producto)
            await self.db.commit()
            await self.db.refresh(producto)
            return ServiceResult(value=producto, status_code=201)
        except Exception as e:
            await self.db.rollback()
            return ServiceResult(error=str(e), status_code=400)

    async def get_all(self) -> List[Producto]:
        result = await self.db.execute(select(Producto).where(Producto.activo == True))
        return result.scalars().all()

    async def get_by_id(self, producto_id: int) -> ServiceResult:
        result = await self.db.execute(
            select(Producto).where(Producto.id == producto_id, Producto.activo == True)
        )
        producto = result.scalars().first()
        if not producto:
            return ServiceResult(error="Producto no encontrado", status_code=404)
        return ServiceResult(value=producto)

    async def update(self, producto_id: int, producto_update: ProductoUpdateRequest) -> ServiceResult:
        result = await self.db.execute(
            select(Producto).where(Producto.id == producto_id, Producto.activo == True)
        )
        producto = result.scalars().first()
        if not producto:
            return ServiceResult(error="Producto no encontrado", status_code=404)

        for var, value in vars(producto_update).items():
            if value is not None:
                setattr(producto, var, value)

        await self.db.commit()
        await self.db.refresh(producto)
        return ServiceResult(value=producto)

    async def soft_delete(self, producto_id: int) -> ServiceResult:
        result = await self.db.execute(
            select(Producto).where(Producto.id == producto_id, Producto.activo == True)
        )
        producto = result.scalars().first()
        if not producto:
            return ServiceResult(error="Producto no encontrado", status_code=404)

        producto.activo = False
        await self.db.commit()
        return ServiceResult(value=producto)

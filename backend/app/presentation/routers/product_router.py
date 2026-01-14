from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.infrastructure.database import get_db
from app.application.product_service import ProductService, ServiceResult
from app.presentation.schemas.product_schemas import ProductoCreateRequest, ProductoUpdateRequest, ProductoResponse

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.post(
    "/",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un producto",
    description="Crea un producto nuevo con todos los campos requeridos.",
    responses={400: {"description": "Datos inválidos del producto"}}
)
async def create_producto(
    producto: ProductoCreateRequest = Body(..., description="Datos del producto a crear"),
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    result: ServiceResult = await service.create(producto)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value

@router.get(
    "/",
    response_model=List[ProductoResponse],
    summary="Obtener todos los productos",
    description="Devuelve la lista de productos activos.",
)
async def get_productos(
    categoria: Optional[int] = Query(None, description="ID de la categoría para filtrar"),
    active: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    return await service.get_all(categoria_id=categoria, active=active)


@router.get(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Obtener un producto por ID",
    description="Devuelve un producto específico por su ID.",
    responses={404: {"description": "Producto no encontrado"}}
)
async def get_producto(
    producto_id: int = Path(..., ge=1, description="ID único del producto"),
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    result: ServiceResult = await service.get_by_id(producto_id)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.put(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Actualizar un producto",
    description="Actualiza los campos de un producto existente.",
    responses={404: {"description": "Producto no encontrado"}}
)
async def update_producto(
    producto_id: int = Path(..., ge=1, description="ID del producto a actualizar"),
    producto: ProductoUpdateRequest = Body(..., description="Campos a actualizar"),
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    result: ServiceResult = await service.update(producto_id, producto)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.delete(
    "/{producto_id}",
    summary="Desactivar (soft delete) un producto",
    description="Marca un producto como inactivo sin eliminarlo físicamente.",
    responses={
        404: {"description": "Producto no encontrado"},
        200: {"description": "Producto desactivado correctamente"}
    }
)
async def delete_producto(
    producto_id: int = Path(..., ge=1, description="ID del producto a desactivar"),
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    result: ServiceResult = await service.soft_delete(producto_id)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return {"detalle": "Producto desactivado correctamente"}

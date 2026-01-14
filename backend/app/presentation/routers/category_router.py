from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.infrastructure.database import get_db
from app.application.category_service import CategoriaService, ServiceResult
from app.presentation.schemas.category_schemas import CategoriaCreateRequest, CategoriaUpdateRequest, CategoriaResponse

router = APIRouter(prefix="/categorias", tags=["Categorías"])


@router.post(
    "/",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una categoría",
    description="Crea una nueva categoría de productos.",
    responses={400: {"description": "Datos inválidos de la categoría"}}
)
async def create_categoria(
    categoria: CategoriaCreateRequest = Body(..., description="Datos de la categoría a crear"),
    db: AsyncSession = Depends(get_db)
):
    service = CategoriaService(db)
    result: ServiceResult = await service.create(categoria)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.get(
    "/",
    response_model=List[CategoriaResponse],
    summary="Obtener todas las categorías",
    description="Devuelve la lista de todas las categorías.",
)
async def get_categorias(db: AsyncSession = Depends(get_db)):
    service = CategoriaService(db)
    return await service.get_all()


@router.get(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Obtener una categoría por ID",
    description="Devuelve una categoría específica por su ID.",
    responses={404: {"description": "Categoría no encontrada"}}
)
async def get_categoria(
    categoria_id: int = Path(..., ge=1, description="ID único de la categoría"),
    db: AsyncSession = Depends(get_db)
):
    service = CategoriaService(db)
    result: ServiceResult = await service.get_by_id(categoria_id)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.put(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Actualizar una categoría",
    description="Actualiza los campos de una categoría existente.",
    responses={404: {"description": "Categoría no encontrada"}}
)
async def update_categoria(
    categoria_id: int = Path(..., ge=1, description="ID de la categoría a actualizar"),
    categoria: CategoriaUpdateRequest = Body(..., description="Campos a actualizar"),
    db: AsyncSession = Depends(get_db)
):
    service = CategoriaService(db)
    result: ServiceResult = await service.update(categoria_id, categoria)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.delete(
    "/{categoria_id}",
    summary="Eliminar una categoría",
    description="Elimina una categoría existente.",
    responses={
        404: {"description": "Categoría no encontrada"},
        200: {"description": "Categoría eliminada correctamente"}
    }
)
async def delete_categoria(
    categoria_id: int = Path(..., ge=1, description="ID de la categoría a eliminar"),
    db: AsyncSession = Depends(get_db)
):
    service = CategoriaService(db)
    result: ServiceResult = await service.delete(categoria_id)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return {"detalle": "Categoría eliminada correctamente"}

from fastapi import APIRouter, Depends, UploadFile, Form, File, HTTPException, status, Path, Query
from dependency_injector.wiring import inject, Provide
from typing import List, Optional
import json

from app.application.product_service import ProductService, ServiceResult
from app.containers import Container
from app.presentation.schemas.product_schemas import ProductoCreateRequest, ProductoUpdateRequest, ProductoResponse

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.post(
    "/",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un producto",
    description="Crea un producto nuevo con precios escalonados.",
    responses={400: {"description": "Datos inválidos del producto"}}
)
@inject
async def create_producto(
    nombre: str = Form(...),
    categoria_id: int = Form(...),
    precios: str = Form(..., description='Ej: [{"cantidad":1,"precio":1200}]'),
    imagen: Optional[UploadFile] = File(None),
    service: ProductService = Depends(Provide[Container.product_service]),
):

    try:
        precios_list = json.loads(precios)
    except json.JSONDecodeError:
        raise HTTPException(400, "El campo precios debe ser JSON válido")

    producto_request = ProductoCreateRequest(
        nombre=nombre,
        categoria_id=categoria_id,
        precios=precios_list
    )

    result: ServiceResult = await service.create(
        producto_request,
        image=imagen
    )

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value

@router.get(
    "/",
    response_model=List[ProductoResponse],
    summary="Obtener todos los productos",
    description="Devuelve la lista de productos.",
)
@inject
async def get_productos(
    categoria: Optional[int] = Query(None, description="ID de la categoría para filtrar"),
    active: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    service: ProductService = Depends(Provide[Container.product_service]),
):
    return await service.get_all(
        categoria_id=categoria,
        active=active
    )



@router.get(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Obtener un producto por ID",
    description="Devuelve un producto específico por su ID.",
    responses={404: {"description": "Producto no encontrado"}}
)
@inject
async def get_producto(
    producto_id: int = Path(..., ge=1, description="ID único del producto"),
    service: ProductService = Depends(Provide[Container.product_service]),
):

    result: ServiceResult = await service.get_by_id(producto_id)
    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value



@router.put(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Actualizar un producto",
    responses={404: {"description": "Producto no encontrado"}}
)
@inject
async def update_producto(
    producto_id: int = Path(..., ge=1),
    nombre: Optional[str] = Form(None),
    categoria_id: Optional[int] = Form(None),
    precios: Optional[str] = Form(
        None,
        description='Ej: [{"cantidad":1,"precio":1200}]'
    ),

    imagen: Optional[UploadFile] = File(None),
    service: ProductService = Depends(Provide[Container.product_service]),
):
    precios_list = None
    if precios is not None:
        try:
            precios_list = json.loads(precios)
        except json.JSONDecodeError:
            raise HTTPException(400, "El campo precios debe ser JSON válido")

    producto_request = ProductoUpdateRequest(
        nombre=nombre,
        categoria_id=categoria_id,
        precios=precios_list
    )

    result: ServiceResult = await service.update(
        producto_id,
        producto_request,
        image=imagen
    )

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value


@router.patch(
    "/{producto_id}/desactivar",
    response_model=ProductoResponse,
    summary="Desactivar un producto",
    responses={404: {"description": "Producto no encontrado"}},
)
@inject
async def deactivate_producto(
    producto_id: int = Path(..., ge=1, description="ID único del producto"),
    service: ProductService = Depends(Provide[Container.product_service]),
):
    result = await service.update(producto_id, active=False)
    
    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )
    
    return result.value

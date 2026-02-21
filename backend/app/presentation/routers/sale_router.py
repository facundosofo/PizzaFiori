from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Request
from fastapi.responses import Response
from dependency_injector.wiring import inject, Provide
from typing import List
from datetime import date

from app.application.sale_service import SaleService, ServiceResult
from app.application.report_service import ReportService
from app.containers import Container
from app.presentation.schemas.sale_schemas import (
    SaleCreateRequest,
    SaleUpdateRequest,
    SaleResponse,
    SaleFilterParams,
    SaleListResponse,
)
from app.presentation.routers.dependencies import get_current_user, require_admin

router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una venta",
    description="Crea una nueva venta con productos y/o ofertas.",
)
@inject
async def create_sale(
    request: Request,
    sale: SaleCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: SaleService = Depends(Provide[Container.sale_service]),
):
    result: ServiceResult = await service.create(
        sale,
        user_id=current_user["id"],
        username=current_user["username"],
    )

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return result.value


@router.get(
    "/",
    response_model=SaleListResponse,
    summary="Obtener todas las ventas",
    description="Devuelve la lista de ventas con paginación, filtros de fecha y total count.",
)
@inject
async def get_sales(
    filters: SaleFilterParams = Depends(),
    service: SaleService = Depends(Provide[Container.sale_service]),
):
    if filters.fecha_desde and filters.fecha_hasta and filters.fecha_desde > filters.fecha_hasta:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="fecha_desde debe ser menor o igual a fecha_hasta",
        )

    sales = await service.get_all(
        skip=filters.skip,
        limit=filters.limit,
        fecha_desde=filters.fecha_desde,
        fecha_hasta=filters.fecha_hasta
    )
    total = await service.count_all(
        fecha_desde=filters.fecha_desde,
        fecha_hasta=filters.fecha_hasta
    )
    return {
        "items": sales,
        "total": total,
        "skip": filters.skip,
        "limit": filters.limit
    }


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Obtener una venta por ID",
    description="Devuelve una venta específica por su ID con nombres de productos/ofertas.",
    responses={404: {"description": "Venta no encontrada"}},
)
@inject
async def get_sale(
    sale_id: int = Path(..., ge=1, description="ID único de la venta"),
    service: SaleService = Depends(Provide[Container.sale_service]),
):
    result: ServiceResult = await service.get_by_id(sale_id)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return result.value


@router.put(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Actualizar una venta",
    description="Actualiza una venta existente. Requiere precio_unitario para cada item.",
    responses={
        404: {"description": "Venta no encontrada"},
        400: {"description": "Datos inválidos - falta precio_unitario en los items"},
        403: {"description": "Admin access required"},
    },
)
@inject
async def update_sale(
    request: Request,
    sale_update: SaleUpdateRequest,
    sale_id: int = Path(..., ge=1, description="ID único de la venta"),
    admin_user: dict = Depends(require_admin),
    service: SaleService = Depends(Provide[Container.sale_service]),
):
    result: ServiceResult = await service.update(
        sale_id, 
        sale_update,
        user_id=admin_user["id"],

        correlation_id=getattr(request.state, "correlation_id", None),
    )

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return result.value


@router.delete(
    "/{sale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una venta",
    description="Elimina una venta existente.",
    responses={
        404: {"description": "Venta no encontrada"},
        403: {"description": "Admin access required"},
    },
)
@inject
async def delete_sale(
    request: Request,
    sale_id: int = Path(..., ge=1, description="ID único de la venta"),
    admin_user: dict = Depends(require_admin),
    service: SaleService = Depends(Provide[Container.sale_service]),
):
    result: ServiceResult = await service.delete(
        sale_id,
        user_id=admin_user["id"],
        username=admin_user["username"],
    )

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return None


@router.get(
    "/reporte/pdf",
    summary="Generar reporte de ventas en PDF",
    description="Genera un reporte PDF con el listado de ventas en el rango seleccionado.",
    responses={
        200: {
            "description": "Reporte PDF generado exitosamente",
            "content": {
                "application/pdf": {
                    "schema": {"type": "string", "format": "binary"}
                }
            }
        },
        404: {"description": "No hay ventas en el período seleccionado"},
        500: {"description": "Error al generar el reporte"},
    },
)
@inject
async def generate_sales_report(
    fecha_desde: date | None = Query(None, description="Fecha inicial del rango (YYYY-MM-DD)"),
    fecha_hasta: date | None = Query(None, description="Fecha final del rango (YYYY-MM-DD)"),
    modo: str = Query("light", description="Modo de color del reporte: 'dark' o 'light'"),
    mostrar_resumen_periodo: bool = Query(True, description="Incluir sección 'Resumen del Período'"),
    mostrar_resumen_dia: bool = Query(True, description="Incluir sección 'Resumen por Día'"),
    mostrar_resumen_categoria: bool = Query(True, description="Incluir sección 'Resumen por Categoría'"),
    mostrar_resumen_productos: bool = Query(True, description="Incluir sección 'Resumen de Productos Vendidos'"),
    mostrar_detalle_ventas: bool = Query(True, description="Incluir sección 'Detalle de Ventas'"),
    report_service: ReportService = Depends(Provide[Container.report_service]),
):
    """
    Genera un reporte PDF con:
    - Resumen del período (total ventas, ingresos)
    - Detalle de cada venta (fecha, orden, items, total)
    """
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="fecha_desde debe ser menor o igual a fecha_hasta",
        )

    result = await report_service.generate_sales_report(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        modo=modo,
        mostrar_resumen_periodo=mostrar_resumen_periodo,
        mostrar_resumen_dia=mostrar_resumen_dia,
        mostrar_resumen_categoria=mostrar_resumen_categoria,
        mostrar_resumen_productos=mostrar_resumen_productos,
        mostrar_detalle_ventas=mostrar_detalle_ventas,
    )

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    # Generar nombre del archivo
    if fecha_desde and fecha_hasta:
        filename = f"reporte_ventas_{fecha_desde}_{fecha_hasta}.pdf"
    elif fecha_desde:
        filename = f"reporte_ventas_desde_{fecha_desde}.pdf"
    elif fecha_hasta:
        filename = f"reporte_ventas_hasta_{fecha_hasta}.pdf"
    else:
        filename = "reporte_ventas.pdf"

    return Response(
        content=result.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from enum import Enum


class TipoPeriodo(str, Enum):
    DIARIO = "daily"
    MENSUAL = "monthly"
    ANUAL = "yearly"


class FiltroTiempo(str, Enum):
    """Filtro de tiempo para análisis de ventas y productos."""
    HOY = "today"
    ULTIMOS_7_DIAS = "last_7_days"
    ULTIMO_MES = "last_month"  # 30 días
    ULTIMO_ANO = "last_year"  # 12 meses
    HISTORICO = "all_time"


class RevenuePorPeriodoResponse(BaseModel):
    """Respuesta para revenue agrupado por período."""
    fecha: str | None = Field(None, description="Fecha (para daily)")
    mes: str | None = Field(None, description="Mes (para monthly)")
    año: str | None = Field(None, description="Año (para yearly)")
    ingresos: float = Field(..., description="Monto total en pesos")
    pedidos: int = Field(..., description="Cantidad de pedidos/órdenes")
    cantidad: int = Field(..., description="Cantidad de items vendidos")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fecha": "2026-02-08",
                "ingresos": 15000.50,
                "pedidos": 5,
                "cantidad": 12
            }
        }
    )


class RevenueEn12MesesResponse(BaseModel):
    """Respuesta para distribución de revenue mensual (12 meses)."""
    mes: str = Field(..., description="Nombre del mes (Ene, Feb, etc)")
    ingresos: float = Field(..., description="Monto total en pesos")
    pedidos: int = Field(..., description="Cantidad de pedidos/órdenes")
    cantidad: int = Field(..., description="Cantidad de items vendidos")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mes": "Ene",
                "ingresos": 45000.0,
                "pedidos": 20,
                "cantidad": 56
            }
        }
    )


class ProductoDestacadoResponse(BaseModel):
    """Respuesta para Ranking de productos."""
    nombre: str = Field(..., description="Nombre del producto")
    categoria: str = Field(..., description="Categoría del producto")
    cantidad: int = Field(..., description="Cantidad total vendida")
    precio: float = Field(..., description="Precio promedio de venta")
    enStock: bool = Field(default=True, description="Indica si está en stock")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Muzzarella",
                "categoria": "Pizzas",
                "cantidad": 45,
                "precio": 1200.0,
                "enStock": True
            }
        }
    )


class VentasPorCategoriaResponse(BaseModel):
    """Respuesta para ventas agrupadas por categoria."""
    categoria: str = Field(..., description="Nombre de la categoria")
    cantidad: int = Field(..., description="Cantidad total vendida")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categoria": "Pizzas",
                "cantidad": 120
            }
        }
    )


class WeekdayRevenueResponse(BaseModel):
    """Respuesta para promedio de revenue por día de semana (con ajuste de horario de negocio)."""
    dia_semana: str = Field(..., description="Nombre del día (Lunes, Martes, etc)")
    promedio_ingresos: float = Field(..., description="Promedio de ingresos para ese día")
    promedio_pedidos: float = Field(..., description="Promedio de pedidos/ventas para ese día")
    promedio_cantidad: float = Field(..., description="Promedio de items vendidos para ese día")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dia_semana": "Lunes",
                "promedio_ingresos": 12500.50,
                "promedio_pedidos": 8.5,
                "promedio_cantidad": 45.5
            }
        }
    )


class GastosPorMesResponse(BaseModel):
    """Respuesta para gastos agrupados por mes."""
    mes: str = Field(..., description="Nombre del mes (Ene 2026, Feb 2026, etc)")
    gastos: float = Field(..., description="Monto total de gastos en pesos")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mes": "Feb 2026",
                "gastos": 32000.0
            }
        }
    )


class GastosPorCategoriaResponse(BaseModel):
    """Respuesta para gastos agrupados por categoria."""
    categoria: str = Field(..., description="Nombre de la categoria")
    gastos: float = Field(..., description="Monto total de gastos en pesos")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categoria": "Servicios",
                "gastos": 18000.0
            }
        }
    )

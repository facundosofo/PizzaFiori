from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from enum import Enum


class TipoPeriodo(str, Enum):
    DIARIO = "daily"
    SEMANAL = "weekly"
    MENSUAL = "monthly"
    ANUAL = "yearly"


class RevenuePorPeriodoResponse(BaseModel):
    """Respuesta para revenue agrupado por período."""
    fecha: str | None = Field(None, description="Fecha (para daily)")
    semana: str | None = Field(None, description="Semana (para weekly)")
    mes: str | None = Field(None, description="Mes (para monthly)")
    año: str | None = Field(None, description="Año (para yearly)")
    ingresos: float = Field(..., description="Monto total en pesos")
    cantidad: int = Field(..., description="Cantidad de items vendidos")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fecha": "2026-02-08",
                "ingresos": 15000.50,
                "cantidad": 12
            }
        }
    )


class RevenueEn12MesesResponse(BaseModel):
    """Respuesta para distribución de revenue mensual (12 meses)."""
    mes: str = Field(..., description="Nombre del mes (Ene, Feb, etc)")
    ingresos: float = Field(..., description="Monto total en pesos")
    cantidad: int = Field(..., description="Cantidad de items vendidos")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mes": "Ene",
                "ingresos": 45000.0,
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


class MetricasDashboardResponse(BaseModel):
    """Respuesta con métricas generales del dashboard."""
    ingresoTotal: float = Field(..., description="Revenue total de todos los tiempos")
    ordenesTotal: int = Field(..., description="Cantidad total de órdenes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingresoTotal": 250000.0,
                "ordenesTotal": 85
            }
        }
    )

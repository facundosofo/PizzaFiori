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
    subcategorias: List['SubcategoriaGastoResponse'] | None = Field(None, description="Subcategorias con sus gastos (opcional)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categoria": "Servicios",
                "gastos": 18000.0,
                "subcategorias": [
                    {"categoria": "Luz", "gastos": 8000.0},
                    {"categoria": "Gas", "gastos": 5000.0},
                ]
            }
        }
    )


class SubcategoriaGastoResponse(BaseModel):
    """Respuesta para subcategoría de gastos."""
    categoria: str = Field(..., description="Nombre de la subcategoría")
    gastos: float = Field(..., description="Monto total de gastos en pesos")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categoria": "Luz",
                "gastos": 8000.0
            }
        }
    )


class GastosPorAnoResponse(BaseModel):
    """Respuesta para gastos agrupados por año."""
    año: str = Field(..., description="Año (2024, 2025, etc)")
    gastos: float = Field(..., description="Monto total de gastos en pesos")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "año": "2025",
                "gastos": 450000.0
            }
        }
    )


class CategoriaMayorCrecimientoResponse(BaseModel):
    """Respuesta para la categoría con mayor crecimiento."""
    categoria: str = Field(..., description="Nombre de la categoría")
    porcentaje: float | None = Field(None, description="Variación porcentual vs período anterior")


class ResumenGastosPeriodoResponse(BaseModel):
    """Resumen de gastos del período para cards del dashboard."""
    resultado_mensual: float = Field(..., description="Total de gastos últimos 30 días")
    variacion_mensual_pct: float | None = Field(None, description="Variación porcentual vs mes anterior")
    comparacion_mes: str = Field(..., description="Mes contra el cual se compara (ej: 'Enero')")
    resultado_anual: float = Field(..., description="Total de gastos últimos 12 meses")
    variacion_anual_pct: float | None = Field(None, description="Variación porcentual vs año anterior")
    comparacion_ano: int = Field(..., description="Año contra el cual se compara (ej: 2025)")
    categoria_mayor_crecimiento: CategoriaMayorCrecimientoResponse | None = Field(
        None,
        description="Categoría con mayor crecimiento vs mes anterior",
    )


class ResumenProductosResponse(BaseModel):
    """Resumen de productos destacados para cards del dashboard."""
    producto_mas_vendido: str = Field(..., description="Nombre del producto más vendido")
    cantidad_mas_vendida: int = Field(..., description="Cantidad vendida del producto más vendido")
    promocion_mas_vendida: str | None = Field(None, description="Nombre de la oferta/promoción más vendida")
    cantidad_promocion: int = Field(default=0, description="Cantidad de promociones vendidas")
    mes_actual: str = Field(..., description="Mes y año actual (ej: 'Febrero 2026')")


class TotalSalesKPIResponse(BaseModel):
    """Respuesta para KPI de Ventas Totales con comparativa."""
    current: float = Field(..., description="Total de ventas del período actual")
    previous: float | None = Field(None, description="Total de ventas del período comparativo (anterior)")
    comparison_type: str | None = Field(None, description="Tipo de comparación: 'YoY', 'MoM', o None si no hay datos comparativos")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current": 125000.50,
                "previous": 98500.25,
                "comparison_type": "YoY"
            }
        }
    )


class TotalExpensesKPIResponse(BaseModel):
    """Respuesta para KPI de Gastos Totales con comparativa."""
    current: float = Field(..., description="Total de gastos del período actual")
    previous: float | None = Field(None, description="Total de gastos del período comparativo (anterior)")
    comparison_type: str | None = Field(None, description="Tipo de comparación: 'YoY', 'MoM', o None si no hay datos comparativos")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current": 85000.75,
                "previous": 72000.50,
                "comparison_type": "MoM"
            }
        }
    )


class NetProfitKPIResponse(BaseModel):
    """Respuesta para KPI de Ganancia Neta con comparativa."""
    sales: float = Field(..., description="Total de ventas del período actual")
    expenses: float = Field(..., description="Total de gastos del período actual")
    net_profit: float = Field(..., description="Ganancia neta (ventas - gastos)")
    previous_net: float | None = Field(None, description="Ganancia neta del período comparativo")
    comparison_type: str | None = Field(None, description="Tipo de comparación: 'YoY', 'MoM', o None")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sales": 125000.50,
                "expenses": 85000.75,
                "net_profit": 39999.75,
                "previous_net": 26499.75,
                "comparison_type": "MoM"
            }
        }
    )


class NetMarginKPIResponse(BaseModel):
    """Respuesta para KPI de Margen Neto porcentual."""
    sales: float = Field(..., description="Total de ventas del período actual")
    expenses: float = Field(..., description="Total de gastos del período actual")
    margin: float = Field(..., description="Margen neto en porcentaje ((ventas - gastos) / ventas * 100)")
    previous_margin: float | None = Field(None, description="Margen neto del período comparativo")
    comparison_type: str | None = Field(None, description="Tipo de comparación: 'YoY', 'MoM', o None")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sales": 125000.50,
                "expenses": 85000.75,
                "margin": 32.0,
                "previous_margin": 26.9,
                "comparison_type": "MoM"
            }
        }
    )


class BalanceMetricsResponse(BaseModel):
    """Respuesta para todas las métricas de balance del período."""
    sales: TotalSalesKPIResponse = Field(..., description="Datos de ventas totales")
    expenses: TotalExpensesKPIResponse = Field(..., description="Datos de gastos totales")
    net_profit: NetProfitKPIResponse = Field(..., description="Datos de ganancia neta")
    net_margin: NetMarginKPIResponse = Field(..., description="Datos de margen neto")



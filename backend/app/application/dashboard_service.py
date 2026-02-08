from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
import structlog
from sqlalchemy import func, select, and_, cast, Date, literal_column, extract, Integer

from app.domain.models.sale import Sale
from app.domain.models.sale_item import SaleItem
from app.domain.models.sale_item_offer_product import SaleItemOfferProduct
from app.domain.models.product import Product
from app.domain.models.category import Category
from app.domain.unit_of_work import AbstractUnitOfWork
from app.presentation.schemas.dashboard_schemas import (
    RevenuePorPeriodoResponse,
    RevenueEn12MesesResponse,
    ProductoDestacadoResponse,
    MetricasDashboardResponse,
    TipoPeriodo,
)


@dataclass
class ServiceResult:
    value: Optional[List | dict] = None
    error: Optional[str] = None
    status_code: int = 200


class DashboardService:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        logger: structlog.BoundLogger | None = None,
    ):
        self.uow = uow
        self.logger = logger or structlog.get_logger(__name__)

    async def get_revenue_by_period(
        self,
        period: TipoPeriodo,
        limit: int = 30,
    ) -> ServiceResult:
        """
        Obtiene el revenue agrupado por período (daily, weekly, monthly, yearly).
        
        Args:
            period: Tipo de período (daily|weekly|monthly|yearly)
            limit: Cantidad máxima de registros a devolver
            
        Returns:
            ServiceResult con lista de RevenueByPeriodResponse
        """
        try:
            async with self.uow:
                result = []
                
                if period == TipoPeriodo.DIARIO:
                    result = await self._get_daily_revenue(limit)
                elif period == TipoPeriodo.SEMANAL:
                    result = await self._get_weekly_revenue(limit)
                elif period == TipoPeriodo.MENSUAL:
                    result = await self._get_monthly_revenue(limit)
                elif period == TipoPeriodo.ANUAL:
                    result = await self._get_yearly_revenue(limit)
                
                return ServiceResult(value=result)
                
        except Exception as e:
            self.logger.error(f"Error obteniendo revenue: {str(e)}")
            return ServiceResult(
                error=f"Error al obtener datos de revenue: {str(e)}",
                status_code=500
            )

    async def get_monthly_revenue(self) -> ServiceResult:
        """
        Obtiene el revenue para cada mes del año (12 registros).
        
        Returns:
            ServiceResult con lista de 12 MonthlyRevenueResponse
        """
        try:
            async with self.uow:
                result = await self._get_monthly_revenue_distribution()
                return ServiceResult(value=result)
                
        except Exception as e:
            self.logger.error(f"Error obteniendo monthly revenue: {str(e)}")
            return ServiceResult(
                error=f"Error al obtener datos mensuales: {str(e)}",
                status_code=500
            )

    async def get_top_products(self, limit: int = 10) -> ServiceResult:
        """
        Obtiene los productos más vendidos.
        
        Args:
            limit: Cantidad máxima de productos a devolver
            
        Returns:
            ServiceResult con lista de TopProductResponse
        """
        try:
            async with self.uow:
                result = await self._get_top_products_data(limit)
                return ServiceResult(value=result)
                
        except Exception as e:
            self.logger.error(f"Error obteniendo top products: {str(e)}")
            return ServiceResult(
                error=f"Error al obtener productos destacados: {str(e)}",
                status_code=500
            )

    async def get_metrics(self) -> ServiceResult:
        """
        Obtiene las métricas generales del dashboard.
        
        Returns:
            ServiceResult con DashboardMetricsResponse
        """
        try:
            async with self.uow:
                metrics = await self._get_dashboard_metrics()
                return ServiceResult(value=metrics)
                
        except Exception as e:
            self.logger.error(f"Error obteniendo metrics: {str(e)}")
            return ServiceResult(
                error=f"Error al obtener métricas: {str(e)}",
                status_code=500
            )

    # === Métodos privados para queries ===

    async def _get_daily_revenue(self, limit: int) -> List[dict]:
        """Agregación diaria del último mes."""
        # Obtener fecha hace 'limit' días
        start_date = datetime.now() - timedelta(days=limit)
        
        query = select(
            cast(Sale.fecha_creacion, Date).label("date"),
            func.sum(Sale.total).label("revenue"),
            func.count(Sale.id).label("orders"),
        ).where(Sale.fecha_creacion >= start_date).group_by(
            cast(Sale.fecha_creacion, Date)
        ).order_by("date")
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "fecha": row.date.strftime("%Y-%m-%d"),
                "ingresos": float(row.revenue or 0),
                "ordenes": row.orders or 0,
            }
            for row in rows
        ]

    async def _get_weekly_revenue(self, limit: int) -> List[dict]:
        """Agregación semanal de las últimas 12 semanas."""
        # Obtener fecha hace (limit * 7) días
        start_date = datetime.now() - timedelta(days=limit * 7)
        
        query = select(
            func.year(Sale.fecha_creacion).label("year"),
            extract('week', Sale.fecha_creacion).label("week"),
            func.sum(Sale.total).label("revenue"),
            func.count(Sale.id).label("orders"),
        ).where(Sale.fecha_creacion >= start_date).group_by(
            func.year(Sale.fecha_creacion),
            extract('week', Sale.fecha_creacion)
        ).order_by("year", "week").limit(limit)
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "semana": f"W{row.week:02d} {datetime.now().strftime('%b')}",
                "ingresos": float(row.revenue or 0),
                "ordenes": row.orders or 0,
            }
            for row in rows
        ]

    async def _get_monthly_revenue(self, limit: int) -> List[dict]:
        """Agregación mensual de los últimos N meses."""
        start_date = datetime.now() - timedelta(days=limit * 30)
        
        query = select(
            func.year(Sale.fecha_creacion).label("year"),
            func.month(Sale.fecha_creacion).label("month"),
            func.sum(Sale.total).label("revenue"),
            func.count(Sale.id).label("orders"),
        ).where(Sale.fecha_creacion >= start_date).group_by(
            func.year(Sale.fecha_creacion),
            func.month(Sale.fecha_creacion)
        ).order_by("year", "month").limit(limit)
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        months = [
            "Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
        ]
        
        return [
            {
                "mes": f"{months[row.month - 1]} {row.year}",
                "ingresos": float(row.revenue or 0),
                "ordenes": row.orders or 0,
            }
            for row in rows
        ]

    async def _get_yearly_revenue(self, limit: int) -> List[dict]:
        """Agregación anual de los últimos 5 años."""
        start_date = datetime.now() - timedelta(days=limit * 365)
        
        query = select(
            func.year(Sale.fecha_creacion).label("year"),
            func.sum(Sale.total).label("revenue"),
            func.count(Sale.id).label("orders"),
        ).where(Sale.fecha_creacion >= start_date).group_by(
            func.year(Sale.fecha_creacion)
        ).order_by("year").limit(limit)
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "año": str(row.year),
                "ingresos": float(row.revenue or 0),
                "ordenes": row.orders or 0,
            }
            for row in rows
        ]

    async def _get_monthly_revenue_distribution(self) -> List[dict]:
        """Distribución de revenue para cada mes (12 meses del año actual)."""
        current_year = datetime.now().year
        
        query = select(
            func.month(Sale.fecha_creacion).label("month"),
            func.sum(Sale.total).label("revenue"),
            func.count(Sale.id).label("orders"),
        ).where(
            func.year(Sale.fecha_creacion) == current_year
        ).group_by(
            func.month(Sale.fecha_creacion)
        ).order_by("month")
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        # Crear diccionario para acceso rápido
        revenue_by_month = {row.month: row for row in rows}
        
        months = [
            "Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
        ]
        
        # Retornar todos los 12 meses (con 0 si no hay datos)
        return [
            {
                "mes": months[i],
                "ingresos": float(revenue_by_month.get(i + 1, {}).revenue or 0)
                    if i + 1 in revenue_by_month else 0,
                "ordenes": revenue_by_month.get(i + 1, {}).orders or 0
                    if i + 1 in revenue_by_month else 0,
            }
            for i in range(12)
        ]

    async def _get_top_products_data(self, limit: int) -> List[dict]:
        """
        Obtiene los productos más vendidos con cantidad total vendida.
        
        Nota: Los datos se obtienen de la tabla SaleItem (snapshots históricos).
        Resuelve nombres de categorías por FK del producto, fallback a item_categoria raw.
        """
        # Query para productos directos con JOIN a categoría por producto
        direct_query = select(
            SaleItem.item_nombre.label("name"),
            func.coalesce(
                Category.nombre,  # Primera opción: nombre de categoría por FK del producto
                SaleItem.item_categoria  # Fallback: valor raw o ID
            ).label("category"),
            func.sum(SaleItem.cantidad).label("total_quantity"),
            func.avg(SaleItem.precio_unitario).label("avg_price"),
        ).outerjoin(
            Product, SaleItem.producto_id == Product.id
        ).outerjoin(
            Category, Product.categoria_id == Category.id
        ).where(
            SaleItem.producto_id.isnot(None)  # Solo productos directos
        ).group_by(
            SaleItem.item_nombre,
            func.coalesce(
                Category.nombre,
                SaleItem.item_categoria
            )
        )

        # Query para productos en ofertas
        offer_query = select(
            SaleItemOfferProduct.producto_nombre.label("name"),
            func.coalesce(
                Category.nombre,  # Primera opción: nombre de categoría por FK del producto
                SaleItemOfferProduct.categoria_nombre  # Fallback: valor raw
            ).label("category"),
            func.sum(SaleItemOfferProduct.cantidad).label("total_quantity"),
        ).outerjoin(
            Product, SaleItemOfferProduct.producto_id == Product.id
        ).outerjoin(
            Category, Product.categoria_id == Category.id
        ).join(
            SaleItem,
            SaleItemOfferProduct.venta_item_id == SaleItem.id
        ).where(
            SaleItem.oferta_id.isnot(None)
        ).group_by(
            SaleItemOfferProduct.producto_nombre,
            func.coalesce(
                Category.nombre,
                SaleItemOfferProduct.categoria_nombre
            )
        )

        direct_result = await self.uow.session.execute(direct_query)
        offer_result = await self.uow.session.execute(offer_query)

        totals: dict[tuple[str | None, str | None], dict] = {}

        # Procesar productos directos
        for row in direct_result.fetchall():
            categoria = row.category or "Sin categoría"
            key = (row.name, categoria)
            totals[key] = {
                "nombre": row.name,
                "categoria": categoria,
                "cantidad": int(row.total_quantity or 0),
                "precio": float(row.avg_price or 0),
                "enStock": True,
            }

        # Procesar ofertas
        for row in offer_result.fetchall():
            category = row.category or "Otras"
            key = (row.name, category)
            if key in totals:
                totals[key]["cantidad"] += int(row.total_quantity or 0)
            else:
                totals[key] = {
                    "nombre": row.name,
                    "categoria": category,
                    "cantidad": int(row.total_quantity or 0),
                    "precio": 0.0,
                    "enStock": True,
                }

        ordered = sorted(
            totals.values(),
            key=lambda item: item["cantidad"],
            reverse=True
        )

        return ordered[:limit]

    async def _get_dashboard_metrics(self) -> dict:
        """Obtiene las métricas generales: total revenue y total orders."""
        # Total revenue
        revenue_query = select(func.sum(Sale.total)).select_from(Sale)
        revenue_result = await self.uow.session.execute(revenue_query)
        total_revenue = revenue_result.scalar() or Decimal("0")
        
        # Total orders
        orders_query = select(func.count(Sale.id)).select_from(Sale)
        orders_result = await self.uow.session.execute(orders_query)
        total_orders = orders_result.scalar() or 0
        
        return {
            "ingresoTotal": float(total_revenue),
            "ordenesTotal": int(total_orders),
        }

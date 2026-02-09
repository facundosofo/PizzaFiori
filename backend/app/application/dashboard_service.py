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
from app.domain.models.product_price import ProductPrice
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

    async def get_top_products(
        self,
        limit: int = 10,
        period: TipoPeriodo = TipoPeriodo.ANUAL,
        sort: str = "top",
        category: str | None = None,
    ) -> ServiceResult:
        """
        Obtiene los productos más/menos vendidos.
        
        Args:
            limit: Cantidad máxima de productos a devolver
            period: Tipo de período
            sort: 'top' para más vendidos, 'bottom' para menos vendidos
            category: Filtrar por categoría (opcional)
            
        Returns:
            ServiceResult con lista de TopProductResponse
        """
        try:
            async with self.uow:
                self.logger.info(f"Getting products with period: {period}, limit: {limit}, sort: {sort}, category: {category}")
                start_date = self._get_start_date_for_period(period)
                self.logger.info(f"Start date calculated: {start_date}")
                result = await self._get_top_products_data(limit, start_date, sort=sort, category=category)
                self.logger.info(f"Products result count: {len(result)}")
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

    async def get_sales_by_category(
        self,
        limit: int | None = None,
        period: TipoPeriodo = TipoPeriodo.ANUAL,
    ) -> ServiceResult:
        """
        Obtiene ventas agrupadas por categoria.

        Args:
            limit: Cantidad maxima de categorias a devolver (opcional)

        Returns:
            ServiceResult con lista de categorias y cantidades
        """
        try:
            async with self.uow:
                self.logger.info(f"Getting sales by category with period: {period}, limit: {limit}")
                start_date = self._get_start_date_for_period(period)
                self.logger.info(f"Start date calculated: {start_date}")
                result = await self._get_sales_by_category_data(limit, start_date)
                self.logger.info(f"Sales by category result count: {len(result)}")
                return ServiceResult(value=result)

        except Exception as e:
            self.logger.error(f"Error obteniendo ventas por categoria: {str(e)}")
            return ServiceResult(
                error=f"Error al obtener ventas por categoria: {str(e)}",
                status_code=500
            )

    # === Métodos privados para queries ===

    def _get_start_date_for_period(self, period: TipoPeriodo) -> datetime:
        self.logger.info(f"Calculating start date for period: {period} (type: {type(period)})")
        if period == TipoPeriodo.DIARIO:
            result = datetime.now() - timedelta(days=30)
            self.logger.info(f"Period is DIARIO, start_date: {result}")
            return result
        if period == TipoPeriodo.SEMANAL:
            result = datetime.now() - timedelta(days=12 * 7)
            self.logger.info(f"Period is SEMANAL, start_date: {result}")
            return result
        if period == TipoPeriodo.MENSUAL:
            result = datetime.now() - timedelta(days=12 * 30)
            self.logger.info(f"Period is MENSUAL, start_date: {result}")
            return result
        result = datetime.now() - timedelta(days=5 * 365)
        self.logger.info(f"Period is ANUAL (default), start_date: {result}")
        return result

    async def _get_daily_revenue(self, limit: int) -> List[dict]:
        """Agregación diaria del último mes."""
        # Obtener fecha hace 'limit' días
        start_date = datetime.now() - timedelta(days=limit)
        
        query = select(
            cast(Sale.fecha_creacion, Date).label("date"),
            func.sum(Sale.total).label("revenue"),
            func.sum(SaleItem.cantidad).label("cantidad"),
        ).select_from(Sale).join(
            SaleItem, Sale.id == SaleItem.venta_id
        ).where(Sale.fecha_creacion >= start_date).group_by(
            cast(Sale.fecha_creacion, Date)
        ).order_by("date")
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "fecha": row.date.strftime("%Y-%m-%d"),
                "ingresos": float(row.revenue or 0),
                "cantidad": int(row.cantidad or 0),
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
            func.sum(SaleItem.cantidad).label("cantidad"),
        ).select_from(Sale).join(
            SaleItem, Sale.id == SaleItem.venta_id
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
                "cantidad": int(row.cantidad or 0),
            }
            for row in rows
        ]

    async def _get_monthly_revenue(self, limit: int) -> List[dict]:
        """Agregación mensual de los últimos N meses."""
        now = datetime.now()

        # Start at the first day of the month, N-1 months ago
        start_year = now.year
        start_month = now.month - (limit - 1)
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        start_date = datetime(start_year, start_month, 1)

        # End at the first day of next month to include current month
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1)
        else:
            end_date = datetime(now.year, now.month + 1, 1)
        
        query = select(
            func.year(Sale.fecha_creacion).label("year"),
            func.month(Sale.fecha_creacion).label("month"),
            func.sum(Sale.total).label("revenue"),
            func.sum(SaleItem.cantidad).label("cantidad"),
        ).select_from(Sale).join(
            SaleItem, Sale.id == SaleItem.venta_id
        ).where(
            and_(
                Sale.fecha_creacion >= start_date,
                Sale.fecha_creacion < end_date,
            )
        ).group_by(
            func.year(Sale.fecha_creacion),
            func.month(Sale.fecha_creacion)
        ).order_by("year", "month").limit(limit)
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        months = [
            "Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
        ]
        
        revenue_by_month = {
            (row.year, row.month): row
            for row in rows
        }

        results: List[dict] = []
        current_year = start_year
        current_month = start_month
        for _ in range(limit):
            row = revenue_by_month.get((current_year, current_month))
            results.append(
                {
                    "mes": f"{months[current_month - 1]} {current_year}",
                    "ingresos": float(row.revenue or 0) if row else 0,
                    "cantidad": int(row.cantidad or 0) if row else 0,
                }
            )

            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1

        return results

    async def _get_yearly_revenue(self, limit: int) -> List[dict]:
        """Agregación anual de los últimos 5 años."""
        start_date = datetime.now() - timedelta(days=limit * 365)
        
        query = select(
            func.year(Sale.fecha_creacion).label("year"),
            func.sum(Sale.total).label("revenue"),
            func.sum(SaleItem.cantidad).label("cantidad"),
        ).select_from(Sale).join(
            SaleItem, Sale.id == SaleItem.venta_id
        ).where(Sale.fecha_creacion >= start_date).group_by(
            func.year(Sale.fecha_creacion)
        ).order_by("year").limit(limit)
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "año": str(row.year),
                "ingresos": float(row.revenue or 0),
                "cantidad": int(row.cantidad or 0),
            }
            for row in rows
        ]

    async def _get_monthly_revenue_distribution(self) -> List[dict]:
        """Distribución de revenue para cada mes (12 meses del año actual)."""
        current_year = datetime.now().year
        
        query = select(
            func.month(Sale.fecha_creacion).label("month"),
            func.sum(Sale.total).label("revenue"),
            func.sum(SaleItem.cantidad).label("cantidad"),
        ).select_from(Sale).join(
            SaleItem, Sale.id == SaleItem.venta_id
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
                "cantidad": int(revenue_by_month.get(i + 1, {}).cantidad or 0)
                    if i + 1 in revenue_by_month else 0,
            }
            for i in range(12)
        ]

    async def _get_top_products_data(
        self,
        limit: int,
        start_date: datetime | None,
        sort: str = "top",
        category: str | None = None,
    ) -> List[dict]:
        """
        Obtiene los productos más/menos vendidos con cantidad total vendida.
        
        Nota: Los datos se obtienen de la tabla SaleItem (snapshots históricos).
        Resuelve nombres de categorías por FK del producto, fallback a item_categoria raw.
        
        Args:
            limit: Cantidad máxima de productos a devolver
            start_date: Fecha de inicio para filtrar (opcional)
            sort: 'top' para descendente (más vendidos), 'bottom' para ascendente (menos vendidos)
            category: Filtrar por categoría (opcional)
        """
        # Query para productos directos con JOIN a categoría por producto
        direct_query = select(
            SaleItem.item_nombre.label("name"),
            func.coalesce(
                Category.nombre,  # Primera opción: nombre de categoría por FK del producto
                SaleItem.item_categoria  # Fallback: valor raw o ID
            ).label("category"),
            func.sum(SaleItem.cantidad).label("total_quantity"),
            func.max(ProductPrice.precio).label("price"),
        ).join(
            Sale, SaleItem.venta_id == Sale.id
        ).outerjoin(
            Product, SaleItem.producto_id == Product.id
        ).outerjoin(
            Category, Product.categoria_id == Category.id
        ).outerjoin(
            ProductPrice,
            and_(
                ProductPrice.producto_id == Product.id,
                ProductPrice.cantidad == 1,
            )
        ).where(
            SaleItem.producto_id.isnot(None)  # Solo productos directos
        ).group_by(
            SaleItem.item_nombre,
            func.coalesce(
                Category.nombre,
                SaleItem.item_categoria
            )
        )

        if start_date is not None:
            direct_query = direct_query.where(Sale.fecha_creacion >= start_date)
        
        # Aplicar filtro de categoría si se proporciona
        if category:
            direct_query = direct_query.where(
                func.coalesce(Category.nombre, SaleItem.item_categoria) == category
            )

        # Query para productos en ofertas
        offer_query = select(
            SaleItemOfferProduct.producto_nombre.label("name"),
            func.coalesce(
                Category.nombre,  # Primera opción: nombre de categoría por FK del producto
                SaleItemOfferProduct.categoria_nombre  # Fallback: valor raw
            ).label("category"),
            func.sum(SaleItemOfferProduct.cantidad).label("total_quantity"),
            func.max(ProductPrice.precio).label("price"),
        ).join(
            SaleItem,
            SaleItemOfferProduct.venta_item_id == SaleItem.id
        ).join(
            Sale, SaleItem.venta_id == Sale.id
        ).outerjoin(
            Product, SaleItemOfferProduct.producto_id == Product.id
        ).outerjoin(
            Category, Product.categoria_id == Category.id
        ).outerjoin(
            ProductPrice,
            and_(
                ProductPrice.producto_id == Product.id,
                ProductPrice.cantidad == 1,
            )
        ).where(
            SaleItem.oferta_id.isnot(None)
        ).group_by(
            SaleItemOfferProduct.producto_nombre,
            func.coalesce(
                Category.nombre,
                SaleItemOfferProduct.categoria_nombre
            )
        )

        if start_date is not None:
            offer_query = offer_query.where(Sale.fecha_creacion >= start_date)
        
        # Aplicar filtro de categoría si se proporciona
        if category:
            offer_query = offer_query.where(
                func.coalesce(Category.nombre, SaleItemOfferProduct.categoria_nombre) == category
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
                "precio": float(row.price or 0),
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
                    "precio": float(row.price or 0),
                    "enStock": True,
                }

        ordered = sorted(
            totals.values(),
            key=lambda item: item["cantidad"],
            reverse=(sort == "top")  # reverse=True para 'top', reverse=False para 'bottom'
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

    async def _get_sales_by_category_data(
        self,
        limit: int | None,
        start_date: datetime | None,
    ) -> List[dict]:
        """Agrega cantidad vendida por categoria (productos directos y en ofertas)."""
        direct_query = select(
            func.coalesce(
                Category.nombre,
                SaleItem.item_categoria
            ).label("category"),
            func.sum(SaleItem.cantidad).label("total_quantity"),
        ).join(
            Sale, SaleItem.venta_id == Sale.id
        ).outerjoin(
            Product, SaleItem.producto_id == Product.id
        ).outerjoin(
            Category, Product.categoria_id == Category.id
        ).where(
            SaleItem.producto_id.isnot(None)
        ).group_by(
            func.coalesce(
                Category.nombre,
                SaleItem.item_categoria
            )
        )

        if start_date is not None:
            direct_query = direct_query.where(Sale.fecha_creacion >= start_date)

        offer_query = select(
            func.coalesce(
                Category.nombre,
                SaleItemOfferProduct.categoria_nombre
            ).label("category"),
            func.sum(SaleItemOfferProduct.cantidad).label("total_quantity"),
        ).join(
            SaleItem,
            SaleItemOfferProduct.venta_item_id == SaleItem.id
        ).join(
            Sale, SaleItem.venta_id == Sale.id
        ).outerjoin(
            Product, SaleItemOfferProduct.producto_id == Product.id
        ).outerjoin(
            Category, Product.categoria_id == Category.id
        ).where(
            SaleItem.oferta_id.isnot(None)
        ).group_by(
            func.coalesce(
                Category.nombre,
                SaleItemOfferProduct.categoria_nombre
            )
        )

        if start_date is not None:
            offer_query = offer_query.where(Sale.fecha_creacion >= start_date)

        direct_result = await self.uow.session.execute(direct_query)
        offer_result = await self.uow.session.execute(offer_query)

        totals: dict[str, int] = {}

        for row in direct_result.fetchall():
            category = row.category or "Sin categoria"
            totals[category] = totals.get(category, 0) + int(row.total_quantity or 0)

        for row in offer_result.fetchall():
            category = row.category or "Sin categoria"
            totals[category] = totals.get(category, 0) + int(row.total_quantity or 0)

        ordered = sorted(
            [
                {
                    "categoria": category,
                    "cantidad": total,
                }
                for category, total in totals.items()
            ],
            key=lambda item: item["cantidad"],
            reverse=True
        )

        if limit is None:
            return ordered

        return ordered[:limit]

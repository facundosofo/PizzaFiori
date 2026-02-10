from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
import structlog
from sqlalchemy import func, select, and_, or_, cast, Date, Float, literal_column, extract, Integer, case, distinct

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
    FiltroTiempo,
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
        Obtiene el revenue agrupado por período (daily, monthly, yearly).
        
        Args:
            period: Tipo de período (daily|monthly|yearly)
            limit: Cantidad máxima de registros a devolver
            
        Returns:
            ServiceResult con lista de RevenueByPeriodResponse
        """
        try:
            async with self.uow:
                result = []
                
                if period == TipoPeriodo.DIARIO:
                    result = await self._get_daily_revenue(limit)
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

    async def get_top_products(
        self,
        limit: int = 10,
        time_filter: FiltroTiempo = FiltroTiempo.HISTORICO,
        sort: str = "top",
        category: str | None = None,
    ) -> ServiceResult:
        """
        Obtiene los productos más/menos vendidos.
        
        Args:
            limit: Cantidad máxima de productos a devolver
            time_filter: Filtro de tiempo (hoy, últimos 7 días, último mes, último año, histórico)
            sort: 'top' para más vendidos, 'bottom' para menos vendidos
            category: Filtrar por categoría (opcional)
            
        Returns:
            ServiceResult con lista de TopProductResponse
        """
        try:
            async with self.uow:
                self.logger.info(f"Getting products with time_filter: {time_filter}, limit: {limit}, sort: {sort}, category: {category}")
                start_date = self._get_start_date_for_time_filter(time_filter)
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
        time_filter: FiltroTiempo = FiltroTiempo.HISTORICO,
    ) -> ServiceResult:
        """
        Obtiene ventas agrupadas por categoria.

        Args:
            limit: Cantidad maxima de categorias a devolver (opcional)
            time_filter: Filtro de tiempo (hoy, últimos 7 días, último mes, último año, histórico)

        Returns:
            ServiceResult con lista de categorias y cantidades
        """
        try:
            async with self.uow:
                self.logger.info(f"Getting sales by category with time_filter: {time_filter}, limit: {limit}")
                start_date = self._get_start_date_for_time_filter(time_filter)
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

    async def get_weekday_revenue(
        self,
        category: str | None = None,
    ) -> ServiceResult:
        """
        Obtiene el promedio de ventas por día de semana (con ajuste de horario de negocio).
        
        El horario de negocio es de 16:00 a 06:00, por lo que las ventas entre
        00:00 y 05:59 se asignan al día anterior (día de negocio que abrió a las 16:00).
        
        Args:
            category: Filtrar por categoría específica (opcional)
            
        Returns:
            ServiceResult con lista de WeekdayRevenueResponse ordenado Lunes a Domingo
        """
        try:
            async with self.uow:
                self.logger.info(f"Getting weekday revenue with category: {category}")
                # Siempre usar 'historic' (sin filtro de fechas)
                result = await self._get_weekday_revenue_data(None, None, category)
                self.logger.info(f"Weekday revenue result count: {len(result)}")
                return ServiceResult(value=result)
                
        except Exception as e:
            self.logger.error(f"Error obteniendo weekday revenue: {str(e)}")
            return ServiceResult(
                error=f"Error al obtener promedio por día de semana: {str(e)}",
                status_code=500
            )

    # === Métodos privados para queries ===

    def _get_start_date_for_period(self, period: TipoPeriodo) -> datetime:
        self.logger.info(f"Calculating start date for period: {period} (type: {type(period)})")
        if period == TipoPeriodo.DIARIO:
            result = datetime.now() - timedelta(days=30)
            self.logger.info(f"Period is DIARIO, start_date: {result}")
            return result
        if period == TipoPeriodo.MENSUAL:
            result = datetime.now() - timedelta(days=12 * 30)
            self.logger.info(f"Period is MENSUAL, start_date: {result}")
            return result
        result = datetime.now() - timedelta(days=5 * 365)
        self.logger.info(f"Period is ANUAL (default), start_date: {result}")
        return result

    def _get_start_date_for_time_filter(self, time_filter: FiltroTiempo) -> datetime | None:
        """
        Calcula la fecha de inicio según el filtro de tiempo.
        
        Returns:
            datetime | None: Fecha de inicio, None para histórico (sin filtro)
        """
        self.logger.info(f"Calculating start date for time filter: {time_filter}")
        now = datetime.now()
        
        if time_filter == FiltroTiempo.HOY:
            # Hoy desde las 00:00:00
            result = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self.logger.info(f"Filter is HOY, start_date: {result}")
            return result
        elif time_filter == FiltroTiempo.ULTIMOS_7_DIAS:
            result = now - timedelta(days=7)
            self.logger.info(f"Filter is ULTIMOS_7_DIAS, start_date: {result}")
            return result
        elif time_filter == FiltroTiempo.ULTIMO_MES:
            result = now - timedelta(days=30)
            self.logger.info(f"Filter is ULTIMO_MES, start_date: {result}")
            return result
        elif time_filter == FiltroTiempo.ULTIMO_ANO:
            result = now - timedelta(days=365)
            self.logger.info(f"Filter is ULTIMO_ANO, start_date: {result}")
            return result
        else:  # HISTORICO
            self.logger.info(f"Filter is HISTORICO, no start_date (all time)")
            return None


    async def _get_daily_revenue(self, limit: int) -> List[dict]:
        """
        Agregación diaria optimizada con horario de negocio.
        
        Optimizaciones aplicadas:
        - Subconsultas para evitar GROUP BY con funciones complejas
        - Pre-filtrado de ventas antes del JOIN
        - Aprovecha índices en fecha_creacion y venta_id
        
        Resta 6 horas a la fecha de creación para que ventas entre 00:00-05:59
        se asignen al día anterior (horario de negocio 16:00 a 06:00).
        """
        from sqlalchemy import text
        
        # Fecha de inicio ajustada
        start_date = datetime.now() - timedelta(days=limit)
        
        # PASO 1: Subconsulta de ventas (pre-filtrado)
        # Calcula la fecha de negocio UNA VEZ por venta
        business_date_expr = cast(
            func.dateadd(text('HOUR'), -6, Sale.fecha_creacion),
            Date
        )
        
        sale_subquery = select(
            Sale.id.label("sale_id"),
            business_date_expr.label("business_date"),
            Sale.total.label("sale_total")
        ).where(
            Sale.fecha_creacion >= start_date
        ).subquery()
        
        # PASO 2: Agregar items por venta
        items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("total_items")
        ).where(
            SaleItem.venta_id.in_(
                select(sale_subquery.c.sale_id)
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        # PASO 3: JOIN y agregación final
        query = select(
            sale_subquery.c.business_date.label("date"),
            func.sum(sale_subquery.c.sale_total).label("revenue"),
            func.count(sale_subquery.c.sale_id).label("pedidos"),
            func.sum(items_subquery.c.total_items).label("cantidad")
        ).select_from(
            sale_subquery
        ).outerjoin(
            items_subquery,
            sale_subquery.c.sale_id == items_subquery.c.venta_id
        ).group_by(
            sale_subquery.c.business_date
        ).order_by(
            sale_subquery.c.business_date
        )
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "fecha": row.date.strftime("%Y-%m-%d"),
                "ingresos": float(row.revenue or 0),
                "pedidos": int(row.pedidos or 0),
                "cantidad": int(row.cantidad or 0),
            }
            for row in rows
        ]

    async def _get_monthly_revenue(self, limit: int) -> List[dict]:
        """Agregación mensual optimizada de los últimos N meses.
        
        Optimizaciones aplicadas:
        - Subconsultas para evitar GROUP BY con funciones complejas
        - Pre-filtrado de ventas antes del JOIN
        - Aprovecha índices en fecha_creacion y venta_id
        """
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
        
        # PASO 1: Subconsulta de ventas (pre-filtrado por rango de fechas)
        sale_subquery = select(
            Sale.id.label("sale_id"),
            func.year(Sale.fecha_creacion).label("year"),
            func.month(Sale.fecha_creacion).label("month"),
            Sale.total.label("sale_total")
        ).where(
            and_(
                Sale.fecha_creacion >= start_date,
                Sale.fecha_creacion < end_date,
            )
        ).subquery()
        
        # PASO 2: Agregar items por venta
        items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("total_items")
        ).where(
            SaleItem.venta_id.in_(
                select(sale_subquery.c.sale_id)
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        # PASO 3: Agregación final por mes
        query = select(
            sale_subquery.c.year,
            sale_subquery.c.month,
            func.sum(sale_subquery.c.sale_total).label("revenue"),
            func.count(sale_subquery.c.sale_id).label("pedidos"),
            func.sum(items_subquery.c.total_items).label("cantidad")
        ).select_from(
            sale_subquery
        ).outerjoin(
            items_subquery,
            sale_subquery.c.sale_id == items_subquery.c.venta_id
        ).group_by(
            sale_subquery.c.year,
            sale_subquery.c.month
        ).order_by(
            sale_subquery.c.year,
            sale_subquery.c.month
        )
        
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
                    "pedidos": int(row.pedidos or 0) if row else 0,
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
        """Agregación anual optimizada de los últimos N años.
        
        Optimizaciones aplicadas:
        - Subconsultas para evitar GROUP BY con funciones complejas
        - Pre-filtrado de ventas antes del JOIN
        - Aprovecha índices en fecha_creacion y venta_id
        """
        start_date = datetime.now() - timedelta(days=limit * 365)
        
        # PASO 1: Subconsulta de ventas (pre-filtrado por fecha)
        sale_subquery = select(
            Sale.id.label("sale_id"),
            func.year(Sale.fecha_creacion).label("year"),
            Sale.total.label("sale_total")
        ).where(
            Sale.fecha_creacion >= start_date
        ).subquery()
        
        # PASO 2: Agregar items por venta
        items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("total_items")
        ).where(
            SaleItem.venta_id.in_(
                select(sale_subquery.c.sale_id)
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        # PASO 3: Agregación final por año
        query = select(
            sale_subquery.c.year,
            func.sum(sale_subquery.c.sale_total).label("revenue"),
            func.count(sale_subquery.c.sale_id).label("pedidos"),
            func.sum(items_subquery.c.total_items).label("cantidad")
        ).select_from(
            sale_subquery
        ).outerjoin(
            items_subquery,
            sale_subquery.c.sale_id == items_subquery.c.venta_id
        ).group_by(
            sale_subquery.c.year
        ).order_by(
            sale_subquery.c.year
        ).limit(limit)
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "año": str(row.year),
                "ingresos": float(row.revenue or 0),
                "pedidos": int(row.pedidos or 0),
                "cantidad": int(row.cantidad or 0),
            }
            for row in rows
        ]


        """Distribución de revenue para cada mes (12 meses del año actual)."""
        current_year = datetime.now().year
        
        query = select(
            func.month(Sale.fecha_creacion).label("month"),
            func.sum(Sale.total).label("revenue"),
            func.count(distinct(Sale.id)).label("pedidos"),
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
                "pedidos": int(revenue_by_month.get(i + 1, {}).pedidos or 0)
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
        Obtiene los productos más/menos vendidos (OPTIMIZADA).
        
        Optimizaciones:
        - UNION ALL en lugar de 2 queries + merge en Python
        - Pre-filtrado de ventas por fecha antes de grandes JOINs
        - Agregación y ordenamiento en SQL para mejor rendimiento
        - Índices en columnas clave (venta_id, categoria_id)
        """
        from sqlalchemy import union_all
        
        # ==== SUBCONSULTA: Pre-filtrar ventas por fecha ====
        # Esto reduce drásticamente el tamaño de los JOINs posteriores
        sales_filtered = select(Sale.id)
        if start_date is not None:
            sales_filtered = sales_filtered.where(Sale.fecha_creacion >= start_date)
        
        sales_subq = sales_filtered.subquery()
        
        # ==== QUERY 1: Productos directos ====
        direct_query = select(
            SaleItem.item_nombre.label("name"),
            func.coalesce(Category.nombre, SaleItem.item_categoria).label("category"),
            func.sum(SaleItem.cantidad).label("total_quantity"),
            func.max(ProductPrice.precio).label("price"),
        ).select_from(
            SaleItem
        ).join(
            sales_subq, SaleItem.venta_id == sales_subq.c.id  # JOIN con ventas pre-filtradas
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
            SaleItem.producto_id.isnot(None)
        )
        
        # Filtro de categoría
        if category:
            direct_query = direct_query.where(
                func.coalesce(Category.nombre, SaleItem.item_categoria) == category
            )
        
        direct_query = direct_query.group_by(
            SaleItem.item_nombre,
            func.coalesce(Category.nombre, SaleItem.item_categoria)
        )
        
        # ==== QUERY 2: Productos en ofertas ====
        offer_query = select(
            SaleItemOfferProduct.producto_nombre.label("name"),
            func.coalesce(Category.nombre, SaleItemOfferProduct.categoria_nombre).label("category"),
            func.sum(SaleItemOfferProduct.cantidad).label("total_quantity"),
            func.max(ProductPrice.precio).label("price"),
        ).select_from(
            SaleItemOfferProduct
        ).join(
            SaleItem, SaleItemOfferProduct.venta_item_id == SaleItem.id
        ).join(
            sales_subq, SaleItem.venta_id == sales_subq.c.id  # JOIN con ventas pre-filtradas
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
        )
        
        # Filtro de categoría
        if category:
            offer_query = offer_query.where(
                func.coalesce(Category.nombre, SaleItemOfferProduct.categoria_nombre) == category
            )
        
        offer_query = offer_query.group_by(
            SaleItemOfferProduct.producto_nombre,
            func.coalesce(Category.nombre, SaleItemOfferProduct.categoria_nombre)
        )
        
        # ==== UNION ALL: Combinar ambas queries ====
        combined_query = union_all(direct_query, offer_query).alias("combined")
        
        # ==== AGREGACIÓN FINAL: Agrupar por nombre+categoría ====
        final_query = select(
            combined_query.c.name,
            combined_query.c.category,
            func.sum(combined_query.c.total_quantity).label("total_quantity"),
            func.max(combined_query.c.price).label("price"),
        ).group_by(
            combined_query.c.name,
            combined_query.c.category
        ).order_by(
            func.sum(combined_query.c.total_quantity).desc() if sort == "top" 
            else func.sum(combined_query.c.total_quantity).asc()
        ).limit(limit)
        
        # ==== EJECUTAR ====
        result = await self.uow.session.execute(final_query)
        rows = result.fetchall()
        
        return [
            {
                "nombre": row.name,
                "categoria": row.category or "Sin categoría",
                "cantidad": int(row.total_quantity or 0),
                "precio": float(row.price or 0),
                "enStock": True,
            }
            for row in rows
        ]

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
        """
        Agrega cantidad vendida por categoría (OPTIMIZADA).
        
        Optimizaciones:
        - UNION ALL en lugar de 2 queries + merge en Python
        - Pre-filtrado de ventas por fecha antes de grandes JOINs
        - Agregación y ordenamiento en SQL
        - Índices en columnas clave (venta_id, categoria_id)
        """
        from sqlalchemy import union_all
        
        # ==== SUBCONSULTA: Pre-filtrar ventas por fecha ====
        # Esto reduce drásticamente el tamaño de los JOINs posteriores
        sales_filtered = select(Sale.id)
        if start_date is not None:
            sales_filtered = sales_filtered.where(Sale.fecha_creacion >= start_date)
        
        sales_subq = sales_filtered.subquery()
        
        # ==== QUERY 1: Productos directos ====
        direct_query = select(
            func.coalesce(
                Category.nombre,
                SaleItem.item_categoria
            ).label("category"),
            func.sum(SaleItem.cantidad).label("total_quantity"),
        ).select_from(
            SaleItem
        ).join(
            sales_subq, SaleItem.venta_id == sales_subq.c.id
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
        
        # ==== QUERY 2: Productos en ofertas ====
        offer_query = select(
            func.coalesce(
                Category.nombre,
                SaleItemOfferProduct.categoria_nombre
            ).label("category"),
            func.sum(SaleItemOfferProduct.cantidad).label("total_quantity"),
        ).select_from(
            SaleItemOfferProduct
        ).join(
            SaleItem,
            SaleItemOfferProduct.venta_item_id == SaleItem.id
        ).join(
            sales_subq, SaleItem.venta_id == sales_subq.c.id
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
        
        # ==== UNION ALL: Combinar ambas queries ====
        combined_query = union_all(direct_query, offer_query).alias("combined")
        
        # ==== AGREGACIÓN FINAL: Agrupar por categoría ====
        final_query = select(
            combined_query.c.category,
            func.sum(combined_query.c.total_quantity).label("total_quantity"),
        ).group_by(
            combined_query.c.category
        ).order_by(
            func.sum(combined_query.c.total_quantity).desc()
        )
        
        if limit is not None:
            final_query = final_query.limit(limit)
        
        # ==== EJECUTAR ====
        result = await self.uow.session.execute(final_query)
        rows = result.fetchall()
        
        return [
            {
                "categoria": row.category or "Sin categoria",
                "cantidad": int(row.total_quantity or 0),
            }
            for row in rows
        ]

    async def _get_weekday_revenue_data(
        self,
        start_date: datetime | None,
        end_date: datetime | None,
        category: str | None = None,
    ) -> List[dict]:
        """
        Obtiene promedio de ingresos y cantidad por día de semana.
        
        Ajusta las fechas restando 6 horas para reflejar el horario de negocio
        (16:00 a 06:00). Esto asegura que ventas entre 00:00-05:59 se asignen
        al día anterior.
        
        Args:
            start_date: Fecha de inicio para filtrar (opcional)
            category: Filtrar por categoría (opcional)
        
        Returns:
            Lista de dicts con dia_semana, promedio_ingresos, promedio_pedidos, promedio_cantidad
        """
        from sqlalchemy import text
        
        # Para MSSQL: calcular el día de semana ajustado (restando 6 horas)
        # DATEPART(WEEKDAY, ...) retorna 1=Sunday, 2=Monday, ..., 7=Saturday
        dow_expression = func.datepart(text('WEEKDAY'), func.dateadd(text('HOUR'), -6, Sale.fecha_creacion))
        business_date_expression = cast(
            func.dateadd(text('HOUR'), -6, Sale.fecha_creacion),
            Date
        )

        # Subconsulta para items de ofertas por SaleItem
        offer_items_query = select(
            SaleItemOfferProduct.venta_item_id,
            func.sum(SaleItemOfferProduct.cantidad).label("offer_items_count")
        ).select_from(SaleItemOfferProduct)

        if category:
            offer_items_query = offer_items_query.outerjoin(
                Product, SaleItemOfferProduct.producto_id == Product.id
            ).outerjoin(
                Category, Product.categoria_id == Category.id
            ).where(
                func.coalesce(Category.nombre, SaleItemOfferProduct.categoria_nombre) == category
            )

        offer_items_subq = offer_items_query.group_by(
            SaleItemOfferProduct.venta_item_id
        ).subquery()

        # Subconsulta: agrupar por venta y calcular totales
        # La cantidad total incluye:
        # - Items directos (SaleItem.cantidad donde producto_id IS NOT NULL)
        # - Items en ofertas (suma de SaleItemOfferProduct.cantidad)
        sale_subquery = select(
            Sale.id.label("sale_id"),
            business_date_expression.label("business_date"),
            dow_expression.label("dow"),
            Sale.total.label("sale_total"),
            func.sum(
                case(
                    (SaleItem.producto_id.isnot(None), SaleItem.cantidad),
                    else_=0
                ) + func.coalesce(offer_items_subq.c.offer_items_count, 0)
            ).label("items_total"),
        ).select_from(Sale).join(
            SaleItem, Sale.id == SaleItem.venta_id
        ).outerjoin(
            offer_items_subq,
            SaleItem.id == offer_items_subq.c.venta_item_id
        )

        # Filtro de período
        if start_date is not None:
            sale_subquery = sale_subquery.where(Sale.fecha_creacion >= start_date)
        if end_date is not None:
            sale_subquery = sale_subquery.where(Sale.fecha_creacion < end_date)

        # Filtro de categoría si se proporciona
        if category:
            sale_subquery = sale_subquery.outerjoin(
                Product, SaleItem.producto_id == Product.id
            ).outerjoin(
                Category, Product.categoria_id == Category.id
            )

            direct_match = and_(
                SaleItem.producto_id.isnot(None),
                func.coalesce(Category.nombre, SaleItem.item_categoria) == category
            )
            offer_match = and_(
                SaleItem.oferta_id.isnot(None),
                offer_items_subq.c.offer_items_count.isnot(None)
            )

            sale_subquery = sale_subquery.where(or_(direct_match, offer_match))

        # GROUP BY: id, total, fecha_creacion y expresiones derivadas
        sale_subquery = sale_subquery.group_by(
            Sale.id,
            Sale.total,
            Sale.fecha_creacion,
            business_date_expression,
            dow_expression
        ).subquery()

        # Agrupar por fecha de negocio
        day_subquery = select(
            sale_subquery.c.business_date,
            sale_subquery.c.dow,
            func.count(sale_subquery.c.sale_id).label("orders_total"),
            func.sum(sale_subquery.c.sale_total).label("ingresos_total"),
            func.sum(sale_subquery.c.items_total).label("items_total"),
        ).group_by(
            sale_subquery.c.business_date,
            sale_subquery.c.dow
        ).subquery()

        # Query principal: agrupar por día de semana y calcular promedios
        # Promedio = SUM(total) / COUNT(días distintos)
        # IMPORTANTE: Cast a Float para evitar división entera en MSSQL
        query = select(
            day_subquery.c.dow,
            (func.sum(day_subquery.c.ingresos_total) / cast(func.count(day_subquery.c.business_date), Float)).label("promedio_ingresos"),
            (func.sum(day_subquery.c.orders_total) / cast(func.count(day_subquery.c.business_date), Float)).label("promedio_pedidos"),
            (func.sum(day_subquery.c.items_total) / cast(func.count(day_subquery.c.business_date), Float)).label("promedio_cantidad"),
        ).group_by(
            day_subquery.c.dow
        ).order_by(
            day_subquery.c.dow
        )
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        # Mapear números a nombres de días en español
        # MSSQL DATEPART(WEEKDAY): 1=Sunday, 2=Monday, 3=Tuesday, ..., 7=Saturday
        dias_semana = {
            1: "Domingo",
            2: "Lunes",
            3: "Martes",
            4: "Miércoles",
            5: "Jueves",
            6: "Viernes",
            7: "Sábado"
        }
        
        # Crear diccionario de resultados por día
        revenue_by_dow = {
            int(row.dow): {
                "dia_semana": dias_semana[int(row.dow)],
                "promedio_ingresos": float(row.promedio_ingresos or 0),
                "promedio_pedidos": float(row.promedio_pedidos or 0),
                "promedio_cantidad": float(row.promedio_cantidad or 0),
            }
            for row in rows
        }
        
        # Retornar ordenado: Lunes (2) a Domingo (1)
        # Orden: 2, 3, 4, 5, 6, 7, 1
        ordered_days = [2, 3, 4, 5, 6, 7, 1]
        return [
            revenue_by_dow.get(dow, {
                "dia_semana": dias_semana[dow],
                "promedio_ingresos": 0.0,
                "promedio_pedidos": 0.0,
                "promedio_cantidad": 0.0,
            })
            for dow in ordered_days
        ]


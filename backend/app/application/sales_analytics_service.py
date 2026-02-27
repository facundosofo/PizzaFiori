"""
Sales Analytics Service - Análisis y reportes de ventas
Incluye revenue por períodos, ventas por categoría, y promedio por día de semana
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
import structlog
from sqlalchemy import func, select, and_, cast, Date, Numeric, extract, Integer

from app.domain.models.sale import Sale
from app.domain.models.sale_item import SaleItem
from app.domain.models.sale_item_offer_product import SaleItemOfferProduct
from app.domain.models.product import Product
from app.domain.models.product_price import ProductPrice
from app.domain.models.product_category import ProductCategory as Category
from app.domain.unit_of_work import AbstractUnitOfWork
from app.presentation.schemas.dashboard_schemas import TipoPeriodo, FiltroTiempo


@dataclass
class ServiceResult:
    value: Optional[List | dict] = None
    error: Optional[str] = None
    status_code: int = 200


class SalesAnalyticsService:
    """Servicio especializado en análisis de ventas"""
    
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
        """Obtiene el revenue agrupado por período (daily, monthly, yearly)"""
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

    async def get_sales_by_category(
        self,
        limit: int | None = None,
        time_filter: FiltroTiempo = FiltroTiempo.HISTORICO,
    ) -> ServiceResult:
        """Obtiene ventas agrupadas por categoría"""
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
        """Obtiene el promedio de ventas por día de semana"""
        try:
            async with self.uow:
                self.logger.info(f"Getting weekday revenue with category: {category}")
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

    def _get_start_date_for_time_filter(self, time_filter: FiltroTiempo) -> datetime | None:
        """Calcula la fecha de inicio según el filtro de tiempo (períodos calendario)."""
        from app.application.analytics_utils import get_start_date_for_time_filter
        result = get_start_date_for_time_filter(time_filter)
        self.logger.info(f"Filter {time_filter} → start_date: {result}")
        return result

    async def _get_daily_revenue(self, limit: int) -> List[dict]:
        """Agregación diaria optimizada con horario de negocio"""
        from sqlalchemy import text
        
        start_date = (datetime.now() - timedelta(days=limit - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        business_date_expr = cast(
            Sale.fecha_creacion - text("INTERVAL '6 hours'"),
            Date
        )
        
        sale_subquery = select(
            Sale.id.label("sale_id"),
            business_date_expr.label("business_date"),
            Sale.total.label("sale_total")
        ).where(
            business_date_expr >= start_date
        ).subquery()
        
        direct_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("direct_qty")
        ).where(
            SaleItem.producto_id.isnot(None)
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        offer_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItemOfferProduct.cantidad * SaleItem.cantidad).label("offer_qty")
        ).select_from(
            SaleItem
        ).join(
            SaleItemOfferProduct, SaleItemOfferProduct.venta_item_id == SaleItem.id
        ).where(
            SaleItem.oferta_id.isnot(None)
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        mitad_mitad_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("mitad_qty")
        ).where(
            SaleItem.es_pizza_mitad_mitad == True
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        query = select(
            sale_subquery.c.business_date.label("date"),
            func.sum(sale_subquery.c.sale_total).label("revenue"),
            func.count(sale_subquery.c.sale_id).label("pedidos"),
            func.sum(
                func.coalesce(direct_items_subquery.c.direct_qty, 0) +
                func.coalesce(offer_items_subquery.c.offer_qty, 0) +
                func.coalesce(mitad_mitad_items_subquery.c.mitad_qty, 0)
            ).label("cantidad")
        ).select_from(
            sale_subquery
        ).outerjoin(
            direct_items_subquery,
            sale_subquery.c.sale_id == direct_items_subquery.c.venta_id
        ).outerjoin(
            offer_items_subquery,
            sale_subquery.c.sale_id == offer_items_subquery.c.venta_id
        ).outerjoin(
            mitad_mitad_items_subquery,
            sale_subquery.c.sale_id == mitad_mitad_items_subquery.c.venta_id
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
        """Agregación mensual optimizada"""
        from sqlalchemy import text

        now = datetime.now()
        start_year = now.year
        start_month = now.month - (limit - 1)
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        start_date = datetime(start_year, start_month, 1)

        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1)
        else:
            end_date = datetime(now.year, now.month + 1, 1)
        
        adjusted_fecha = Sale.fecha_creacion - text("INTERVAL '6 hours'")
        sale_subquery = select(
            Sale.id.label("sale_id"),
            extract('year', adjusted_fecha).label("year"),
            extract('month', adjusted_fecha).label("month"),
            Sale.total.label("sale_total")
        ).where(
            and_(
                adjusted_fecha >= start_date,
                adjusted_fecha < end_date,
            )
        ).subquery()
        
        direct_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("direct_qty")
        ).where(
            and_(
                SaleItem.venta_id.in_(select(sale_subquery.c.sale_id)),
                SaleItem.producto_id.isnot(None)
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        offer_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItemOfferProduct.cantidad * SaleItem.cantidad).label("offer_qty")
        ).select_from(
            SaleItem
        ).join(
            SaleItemOfferProduct, SaleItemOfferProduct.venta_item_id == SaleItem.id
        ).where(
            and_(
                SaleItem.venta_id.in_(select(sale_subquery.c.sale_id)),
                SaleItem.oferta_id.isnot(None)
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        mitad_mitad_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("mitad_qty")
        ).where(
            and_(
                SaleItem.venta_id.in_(select(sale_subquery.c.sale_id)),
                SaleItem.es_pizza_mitad_mitad == True
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        query = select(
            sale_subquery.c.year,
            sale_subquery.c.month,
            func.sum(sale_subquery.c.sale_total).label("revenue"),
            func.count(sale_subquery.c.sale_id).label("pedidos"),
            func.sum(
                func.coalesce(direct_items_subquery.c.direct_qty, 0) +
                func.coalesce(offer_items_subquery.c.offer_qty, 0) +
                func.coalesce(mitad_mitad_items_subquery.c.mitad_qty, 0)
            ).label("cantidad")
        ).select_from(
            sale_subquery
        ).outerjoin(
            direct_items_subquery,
            sale_subquery.c.sale_id == direct_items_subquery.c.venta_id
        ).outerjoin(
            offer_items_subquery,
            sale_subquery.c.sale_id == offer_items_subquery.c.venta_id
        ).outerjoin(
            mitad_mitad_items_subquery,
            sale_subquery.c.sale_id == mitad_mitad_items_subquery.c.venta_id
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
        """Agregación anual optimizada - retorna últimos N años completamente, incluyendo años con 0 ingresos"""
        from sqlalchemy import text

        now = datetime.now()
        current_year = now.year
        start_year = current_year - (limit - 1)  # Últimos N años incluyendo el actual
        
        adjusted_fecha = Sale.fecha_creacion - text("INTERVAL '6 hours'")
        
        # Subquery de ventas dentro del rango de años
        sale_subquery = select(
            Sale.id.label("sale_id"),
            extract('year', adjusted_fecha).label("year"),
            Sale.total.label("sale_total")
        ).where(
            extract('year', adjusted_fecha) >= start_year
        ).subquery()
        
        direct_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("direct_qty")
        ).where(
            and_(
                SaleItem.venta_id.in_(select(sale_subquery.c.sale_id)),
                SaleItem.producto_id.isnot(None)
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        offer_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItemOfferProduct.cantidad * SaleItem.cantidad).label("offer_qty")
        ).select_from(
            SaleItem
        ).join(
            SaleItemOfferProduct, SaleItemOfferProduct.venta_item_id == SaleItem.id
        ).where(
            and_(
                SaleItem.venta_id.in_(select(sale_subquery.c.sale_id)),
                SaleItem.oferta_id.isnot(None)
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        mitad_mitad_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("mitad_qty")
        ).where(
            and_(
                SaleItem.venta_id.in_(select(sale_subquery.c.sale_id)),
                SaleItem.es_pizza_mitad_mitad == True
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        # Consulta de años con agregación
        query = select(
            sale_subquery.c.year,
            func.sum(sale_subquery.c.sale_total).label("revenue"),
            func.count(sale_subquery.c.sale_id).label("pedidos"),
            func.sum(
                func.coalesce(direct_items_subquery.c.direct_qty, 0) +
                func.coalesce(offer_items_subquery.c.offer_qty, 0) +
                func.coalesce(mitad_mitad_items_subquery.c.mitad_qty, 0)
            ).label("cantidad")
        ).select_from(
            sale_subquery
        ).outerjoin(
            direct_items_subquery,
            sale_subquery.c.sale_id == direct_items_subquery.c.venta_id
        ).outerjoin(
            offer_items_subquery,
            sale_subquery.c.sale_id == offer_items_subquery.c.venta_id
        ).outerjoin(
            mitad_mitad_items_subquery,
            sale_subquery.c.sale_id == mitad_mitad_items_subquery.c.venta_id
        ).group_by(
            sale_subquery.c.year
        ).order_by(
            sale_subquery.c.year
        )
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        # Crear diccionario de años con datos
        year_data = {int(row.year): {
            "año": str(int(row.year)),
            "ingresos": float(row.revenue or 0),
            "pedidos": int(row.pedidos or 0),
            "cantidad": int(row.cantidad or 0),
        } for row in rows}
        
        # Agregar años faltantes con 0 en ingresos
        result_list = []
        for year in range(start_year, current_year + 1):
            if year in year_data:
                result_list.append(year_data[year])
            else:
                result_list.append({
                    "año": str(year),
                    "ingresos": 0.0,
                    "pedidos": 0,
                    "cantidad": 0,
                })
        
        return result_list

    async def _get_sales_by_category_data(
        self,
        limit: int | None,
        start_date: datetime | None,
    ) -> List[dict]:
        """Agrega cantidad vendida por categoría"""
        from sqlalchemy import union_all, text
        
        adjusted_fecha = Sale.fecha_creacion - text("INTERVAL '6 hours'")
        business_date_expr = cast(adjusted_fecha, Date)
        sales_filtered = select(Sale.id)
        
        if start_date is not None:
            sales_filtered = sales_filtered.where(business_date_expr >= cast(start_date, Date))
        
        sales_subq = sales_filtered.subquery()
        
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
        
        offer_query = select(
            func.coalesce(
                Category.nombre,
                SaleItemOfferProduct.categoria_nombre
            ).label("category"),
            func.sum(SaleItemOfferProduct.cantidad * SaleItem.cantidad).label("total_quantity"),
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
        
        pizza_mitad_query = select(
            SaleItem.item_categoria.label("category"),
            func.sum(SaleItem.cantidad).label("total_quantity"),
        ).select_from(
            SaleItem
        ).join(
            sales_subq, SaleItem.venta_id == sales_subq.c.id
        ).where(
            SaleItem.es_pizza_mitad_mitad == True
        ).group_by(
            SaleItem.item_categoria
        )
        
        combined_query = union_all(direct_query, offer_query, pizza_mitad_query).alias("combined")
        
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
        """Obtiene promedio de ingresos y cantidad por día de semana"""
        from sqlalchemy import text
        
        adjusted_fecha = Sale.fecha_creacion - text("INTERVAL '6 hours'")
        
        sales_filter = select(Sale.id)
        if start_date is not None:
            sales_filter = sales_filter.where(Sale.fecha_creacion >= start_date)
        if end_date is not None:
            sales_filter = sales_filter.where(Sale.fecha_creacion < end_date)
        
        sales_subq = sales_filter.subquery()
        
        direct_items_query = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("direct_qty")
        ).select_from(SaleItem).join(
            sales_subq, SaleItem.venta_id == sales_subq.c.id
        ).where(
            SaleItem.producto_id.isnot(None)
        )
        
        if category:
            direct_items_query = direct_items_query.outerjoin(
                Product, SaleItem.producto_id == Product.id
            ).outerjoin(
                Category, Product.categoria_id == Category.id
            ).where(
                func.coalesce(Category.nombre, SaleItem.item_categoria) == category
            )
        
        direct_items_query = direct_items_query.group_by(SaleItem.venta_id).subquery()
        
        offer_items_query = select(
            SaleItem.venta_id,
            func.sum(SaleItemOfferProduct.cantidad).label("offer_qty")
        ).select_from(SaleItem).join(
            SaleItemOfferProduct, SaleItemOfferProduct.venta_item_id == SaleItem.id
        ).join(
            sales_subq, SaleItem.venta_id == sales_subq.c.id
        ).where(
            SaleItem.oferta_id.isnot(None)
        )
        
        if category:
            offer_items_query = offer_items_query.outerjoin(
                Product, SaleItemOfferProduct.producto_id == Product.id
            ).outerjoin(
                Category, Product.categoria_id == Category.id
            ).where(
                func.coalesce(Category.nombre, SaleItemOfferProduct.categoria_nombre) == category
            )
        
        offer_items_query = offer_items_query.group_by(SaleItem.venta_id).subquery()
        
        mitad_mitad_items_query = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("mitad_mitad_qty")
        ).select_from(SaleItem).join(
            sales_subq, SaleItem.venta_id == sales_subq.c.id
        ).where(
            and_(
                SaleItem.es_pizza_mitad_mitad == True,
                SaleItem.producto_id.is_(None),
                SaleItem.oferta_id.is_(None)
            )
        )
        
        if category:
            mitad_mitad_items_query = mitad_mitad_items_query.where(
                SaleItem.item_categoria == category
            )
        
        mitad_mitad_items_query = mitad_mitad_items_query.group_by(SaleItem.venta_id).subquery()
        
        sale_daily_data = select(
            Sale.id.label("sale_id"),
            cast(adjusted_fecha, Date).label("business_date"),
            (extract('dow', adjusted_fecha) + 1).label("dow"),
            Sale.total.label("revenue"),
            (func.coalesce(direct_items_query.c.direct_qty, 0) + 
             func.coalesce(offer_items_query.c.offer_qty, 0) + 
             func.coalesce(mitad_mitad_items_query.c.mitad_mitad_qty, 0)).label("total_items")
        ).select_from(Sale).join(
            sales_subq, Sale.id == sales_subq.c.id
        ).outerjoin(
            direct_items_query, Sale.id == direct_items_query.c.venta_id
        ).outerjoin(
            offer_items_query, Sale.id == offer_items_query.c.venta_id
        ).outerjoin(
            mitad_mitad_items_query, Sale.id == mitad_mitad_items_query.c.venta_id
        ).subquery()
        
        daily_summary = select(
            sale_daily_data.c.business_date,
            sale_daily_data.c.dow,
            func.count(sale_daily_data.c.sale_id).label("orders_count"),
            func.sum(sale_daily_data.c.revenue).label("daily_revenue"),
            func.sum(sale_daily_data.c.total_items).label("daily_items")
        ).group_by(
            sale_daily_data.c.business_date,
            sale_daily_data.c.dow
        ).subquery()
        
        query = select(
            daily_summary.c.dow,
            (func.sum(daily_summary.c.daily_revenue) / cast(func.count(daily_summary.c.business_date), Numeric)).label("promedio_ingresos"),
            (func.sum(daily_summary.c.orders_count) / cast(func.count(daily_summary.c.business_date), Numeric)).label("promedio_pedidos"),
            (func.sum(daily_summary.c.daily_items) / cast(func.count(daily_summary.c.business_date), Numeric)).label("promedio_cantidad"),
        ).group_by(
            daily_summary.c.dow
        ).order_by(
            daily_summary.c.dow
        )
        
        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        
        dias_semana = {
            1: "Domingo",
            2: "Lunes",
            3: "Martes",
            4: "Miércoles",
            5: "Jueves",
            6: "Viernes",
            7: "Sábado"
        }
        
        revenue_by_dow = {
            int(row.dow): {
                "dia_semana": dias_semana[int(row.dow)],
                "promedio_ingresos": float(row.promedio_ingresos or 0),
                "promedio_pedidos": float(row.promedio_pedidos or 0),
                "promedio_cantidad": float(row.promedio_cantidad or 0),
            }
            for row in rows
        }
        
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

    async def get_total_sales_with_comparison(
        self,
        days_in_period: int = 30,
    ) -> ServiceResult:
        """
        Obtiene el total de ventas del período actual con comparativa.
        
        Compara mes calendario actual (1° hasta hoy) vs mes calendario anterior (1° hasta mismo día).
        
        Args:
            days_in_period: Ignorado (mantenido por compatibilidad)
            
        Returns:
            ServiceResult con TotalSalesKPIResponse
        """
        try:
            async with self.uow:
                now = datetime.now()
                
                # Período actual: 1° del mes actual hasta hoy
                current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                current_end = now
                
                # Obtener ventas del período actual
                current_total = await self._get_sales_total_between_dates(current_start, current_end)

                # Período anterior: 1° del mes anterior hasta el mismo día del mes anterior
                # Calcular el mes anterior
                if now.month == 1:
                    prev_year = now.year - 1
                    prev_month = 12
                else:
                    prev_year = now.year
                    prev_month = now.month - 1
                
                mom_start = datetime(prev_year, prev_month, 1, 0, 0, 0, 0)
                try:
                    mom_end = datetime(prev_year, prev_month, now.day, 23, 59, 59, 999999)
                except ValueError:
                    # El mes anterior no tiene el mismo día (e.g., 31 enero -> 28/29 febrero)
                    # Usar el último día del mes anterior
                    if prev_month == 2:
                        # Febrero: verificar año bisiesto
                        is_leap = (prev_year % 4 == 0 and prev_year % 100 != 0) or (prev_year % 400 == 0)
                        last_day = 29 if is_leap else 28
                    elif prev_month in [4, 6, 9, 11]:
                        last_day = 30
                    else:
                        last_day = 31
                    mom_end = datetime(prev_year, prev_month, last_day, 23, 59, 59, 999999)
                
                mom_total = await self._get_sales_total_between_dates(mom_start, mom_end)

                comparison_type = None
                previous_total = None
                if mom_total is not None and mom_total > 0:
                    previous_total = mom_total
                    comparison_type = "MoM"
                
                return ServiceResult(
                    value={
                        "current": float(current_total or 0),
                        "previous": float(previous_total) if previous_total else None,
                        "comparison_type": comparison_type,
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Error obteniendo total de ventas con comparativa: {str(e)}")
            return ServiceResult(
                error=f"Error al obtener total de ventas: {str(e)}",
                status_code=500
            )

    async def _get_sales_total_between_dates(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> float | None:
        """
        Obtiene el total de ventas entre dos fechas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Total de ventas en pesos, o None si no hay datos
        """
        try:
            query = select(
                func.sum(Sale.total).label("total_sales")
            ).where(
                and_(
                    Sale.fecha_creacion >= start_date,
                    Sale.fecha_creacion < end_date
                )
            )
            
            result = await self.uow.session.execute(query)
            row = result.scalar_one_or_none()
            
            return row if row is not None else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculando total de ventas entre {start_date} y {end_date}: {str(e)}")
            return None

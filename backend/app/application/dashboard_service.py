from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
import structlog
from sqlalchemy import func, select, and_, cast, Date, Numeric, distinct, extract

from app.domain.models.sale import Sale
from app.domain.models.sale_item import SaleItem
from app.domain.models.sale_item_offer_product import SaleItemOfferProduct
from app.domain.models.product import Product
from app.domain.models.product_price import ProductPrice
from app.domain.models.category import Category
from app.domain.unit_of_work import AbstractUnitOfWork
from app.presentation.schemas.dashboard_schemas import TipoPeriodo, FiltroTiempo


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
                result = await self._get_top_products_data(
                    limit,
                    start_date,
                    sort=sort,
                    category=category,
                )
                self.logger.info(f"Products result count: {len(result)}")
                return ServiceResult(value=result)
                
        except Exception as e:
            self.logger.error(f"Error obteniendo top products: {str(e)}")
            return ServiceResult(
                error=f"Error al obtener productos destacados: {str(e)}",
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

    def _get_start_date_for_time_filter(self, time_filter: FiltroTiempo) -> datetime | None:
        """
        Calcula la fecha de inicio según el filtro de tiempo.
        
        Nota: El "shift" real de -6h (ajuste de horario de negocio) lo hace SQL con dateadd().
        Este método define el rango calendario del filtro. El ajuste temporal se aplica en la query.
        
        Returns:
            datetime | None: Fecha de inicio, None para histórico (sin filtro)
        """
        self.logger.info(f"Calculating start date for time filter: {time_filter}")
        now = datetime.now()
        
        if time_filter == FiltroTiempo.HOY:
            # Inicio del rango: hoy desde las 00:00:00
            # El ajuste de -6h lo hace SQL (dateadd), no Python
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
        
        # Fecha de inicio ajustada (incluye el día actual)
        start_date = (datetime.now() - timedelta(days=limit - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # PASO 1: Subconsulta de ventas (pre-filtrado)
        # Calcula la fecha de negocio UNA VEZ por venta
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
        
        # PASO 2: Agregar items DIRECTOS por venta (productos individuales)
        direct_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("direct_qty")
        ).where(
            SaleItem.producto_id.isnot(None)  # Productos directos
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        # PASO 3: Agregar items de OFERTAS por venta (cantidad de productos en oferta * cantidad de ofertas)
        offer_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItemOfferProduct.cantidad * SaleItem.cantidad).label("offer_qty")
        ).select_from(
            SaleItem
        ).join(
            SaleItemOfferProduct, SaleItemOfferProduct.venta_item_id == SaleItem.id
        ).where(
            SaleItem.oferta_id.isnot(None)  # Items de ofertas
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        # PASO 4: Agregar items MITAD-MITAD por venta
        mitad_mitad_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("mitad_qty")
        ).where(
            SaleItem.es_pizza_mitad_mitad == True
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        # PASO 5: JOIN y agregación final
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
        """Agregación mensual optimizada de los últimos N meses.
        
        Optimizaciones aplicadas:
        - Subconsultas para evitar GROUP BY con funciones complejas
        - Pre-filtrado de ventas antes del JOIN
        - Aprovecha índices en fecha_creacion y venta_id
        """
        from sqlalchemy import text

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
        
        # PASO 2: Agregar items DIRECTOS por venta (productos individuales)
        direct_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("direct_qty")
        ).where(
            and_(
                SaleItem.venta_id.in_(select(sale_subquery.c.sale_id)),
                SaleItem.producto_id.isnot(None)  # Productos directos
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        # PASO 3: Agregar items de OFERTAS por venta (cantidad de productos en oferta * cantidad de ofertas)
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
                SaleItem.oferta_id.isnot(None)  # Items de ofertas
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        # PASO 4: Agregar items MITAD-MITAD por venta
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
        
        # PASO 5: Agregación final por mes
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
        """Agregación anual optimizada de los últimos N años.
        
        Optimizaciones aplicadas:
        - Subconsultas para evitar GROUP BY con funciones complejas
        - Pre-filtrado de ventas antes del JOIN
        - Aprovecha índices en fecha_creacion y venta_id
        """
        from sqlalchemy import text

        start_date = datetime.now() - timedelta(days=limit * 365)
        
        # PASO 1: Subconsulta de ventas (pre-filtrado por fecha)
        adjusted_fecha = Sale.fecha_creacion - text("INTERVAL '6 hours'")
        sale_subquery = select(
            Sale.id.label("sale_id"),
            extract('year', adjusted_fecha).label("year"),
            Sale.total.label("sale_total")
        ).where(
            adjusted_fecha >= start_date
        ).subquery()
        
        # PASO 2: Agregar items DIRECTOS por venta (productos individuales)
        direct_items_subquery = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("direct_qty")
        ).where(
            and_(
                SaleItem.venta_id.in_(select(sale_subquery.c.sale_id)),
                SaleItem.producto_id.isnot(None)  # Productos directos
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        # PASO 3: Agregar items de OFERTAS por venta (cantidad de productos en oferta * cantidad de ofertas)
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
                SaleItem.oferta_id.isnot(None)  # Items de ofertas
            )
        ).group_by(
            SaleItem.venta_id
        ).subquery()
        
        # PASO 4: Agregar items MITAD-MITAD por venta
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
        
        # PASO 5: Agregación final por año
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
        - UNION ALL en lugar de 3 queries + merge en Python (productos directos, ofertas, pizzas mitad/mitad)
        - Pre-filtrado de ventas por fecha antes de grandes JOINs
        - Agregación y ordenamiento en SQL para mejor rendimiento
        - Índices en columnas clave (venta_id, categoria_id, es_pizza_mitad_mitad)
        - COHERENCIA: Todos los filtros usan adjusted_fecha (horario de negocio 16:00-06:00)
        """
        from sqlalchemy import union_all, text
        
        # ==== SUBCONSULTA: Pre-filtrar ventas por fecha (ajustada a día de negocio) ====
        # Esto reduce drásticamente el tamaño de los JOINs posteriores
        #  COHERENCIA: Todos los filtros (HOY, ULTIMOS_7_DIAS, etc) usan adjusted_fecha
        adjusted_fecha = Sale.fecha_creacion - text("INTERVAL '6 hours'")
        business_date_expr = cast(adjusted_fecha, Date)
        sales_filtered = select(Sale.id)
        
        if start_date is not None:
            # Misma lógica para todos: comparar fechas de negocio como Date
            sales_filtered = sales_filtered.where(business_date_expr >= cast(start_date, Date))
        
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
            func.sum(SaleItemOfferProduct.cantidad * SaleItem.cantidad).label("total_quantity"),
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
        
        # ==== QUERY 3: Pizzas mitad/mitad ====
        mitad_mitad_query = select(
            SaleItem.item_nombre.label("name"),
            SaleItem.item_categoria.label("category"),
            func.sum(SaleItem.cantidad).label("total_quantity"),
            SaleItem.precio_unitario.label("price"),
        ).select_from(
            SaleItem
        ).join(
            sales_subq, SaleItem.venta_id == sales_subq.c.id  # JOIN con ventas pre-filtradas
        ).where(
            and_(
                SaleItem.es_pizza_mitad_mitad == True,
                SaleItem.producto_id.is_(None),
                SaleItem.oferta_id.is_(None)
            )
        )
        
        # Filtro de categoría
        if category:
            mitad_mitad_query = mitad_mitad_query.where(
                SaleItem.item_categoria == category
            )
        
        mitad_mitad_query = mitad_mitad_query.group_by(
            SaleItem.item_nombre,
            SaleItem.item_categoria,
            SaleItem.precio_unitario
        )
        
        # ==== UNION ALL: Combinar las tres queries ====
        combined_query = union_all(direct_query, offer_query, mitad_mitad_query).alias("combined")
        
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


    async def _get_sales_by_category_data(
        self,
        limit: int | None,
        start_date: datetime | None,
    ) -> List[dict]:
        """
        Agrega cantidad vendida por categoría (OPTIMIZADA).
        
        Optimizaciones:
        - UNION ALL en lugar de 3 queries + merge en Python
        - Pre-filtrado de ventas por fecha antes de grandes JOINs
        - Agregación y ordenamiento en SQL
        - Índices en columnas clave (venta_id, categoria_id)
        - ✅ COHERENCIA: Todos los filtros usan adjusted_fecha (horario de negocio 16:00-06:00)
        - ✅ PIZZAS MITAD-MITAD: Incluye query específica para pizzas mitad-mitad
        """
        from sqlalchemy import union_all, text
        
        # ==== SUBCONSULTA: Pre-filtrar ventas por fecha (ajustada a día de negocio) ====
        # Esto reduce drásticamente el tamaño de los JOINs posteriores
        # COHERENCIA: Todos los filtros (HOY, ULTIMOS_7_DIAS, etc) usan adjusted_fecha
        adjusted_fecha = Sale.fecha_creacion - text("INTERVAL '6 hours'")
        business_date_expr = cast(adjusted_fecha, Date)
        sales_filtered = select(Sale.id)
        
        if start_date is not None:
            # Misma lógica para todos: comparar fechas de negocio como Date
            sales_filtered = sales_filtered.where(business_date_expr >= cast(start_date, Date))
        
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
        
        # ==== QUERY 3: Pizzas Mitad-Mitad ====
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
        
        # ==== UNION ALL: Combinar las tres queries ====
        combined_query = union_all(direct_query, offer_query, pizza_mitad_query).alias("combined")
        
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
        Obtiene promedio de ingresos y cantidad por día de semana (OPTIMIZADA).
        
        Optimizaciones principales:
        - Pre-filtrado de ventas por fecha ANTES de grandes JOINs
        - Separación de queries directas vs ofertas vs pizzas mitad/mitad (en lugar de CASE complejo)
        - Subconsultas simples y reutilizables
        - Agregación en SQL completa, sin procesamiento en Python
        
        Ajusta las fechas restando 6 horas para reflejar el horario de negocio
        (16:00 a 06:00). Esto asegura que ventas entre 00:00-05:59 se asignen
        al día anterior.
        """
        from sqlalchemy import text
        
        # PASO 1: CTE para fecha+hora de negocio (reutilizable en la query)
        # Resta 6 horas para convertir a horario de negocio (16:00 a 06:00)
        adjusted_fecha = Sale.fecha_creacion - text("INTERVAL '6 hours'")
        
        # PASO 2: Pre-filtrar ventas por fecha (índice en fecha_creacion)
        sales_filter = select(Sale.id)
        if start_date is not None:
            sales_filter = sales_filter.where(Sale.fecha_creacion >= start_date)
        if end_date is not None:
            sales_filter = sales_filter.where(Sale.fecha_creacion < end_date)
        
        sales_subq = sales_filter.subquery()
        
        # PASO 3: Agregación de items DIRECTOS por venta (usando JOIN explícito en lugar de IN)
        direct_items_query = select(
            SaleItem.venta_id,
            func.sum(SaleItem.cantidad).label("direct_qty")
        ).select_from(SaleItem).join(
            sales_subq, SaleItem.venta_id == sales_subq.c.id
        ).where(
            SaleItem.producto_id.isnot(None)
        )
        
        # Aplicar filtro de categoría para items directos
        if category:
            direct_items_query = direct_items_query.outerjoin(
                Product, SaleItem.producto_id == Product.id
            ).outerjoin(
                Category, Product.categoria_id == Category.id
            ).where(
                func.coalesce(Category.nombre, SaleItem.item_categoria) == category
            )
        
        direct_items_query = direct_items_query.group_by(SaleItem.venta_id).subquery()
        
        # PASO 4: Agregación de items en OFERTAS por venta (usando JOIN explícito en lugar de IN)
        offer_items_query = select(
            SaleItem.venta_id,
            func.sum(SaleItemOfferProduct.cantidad * SaleItem.cantidad).label("offer_qty")
        ).select_from(SaleItem).join(
            SaleItemOfferProduct, SaleItemOfferProduct.venta_item_id == SaleItem.id
        ).join(
            sales_subq, SaleItem.venta_id == sales_subq.c.id
        ).where(
            SaleItem.oferta_id.isnot(None)
        )
        
        # Aplicar filtro de categoría para items en ofertas
        if category:
            offer_items_query = offer_items_query.outerjoin(
                Product, SaleItemOfferProduct.producto_id == Product.id
            ).outerjoin(
                Category, Product.categoria_id == Category.id
            ).where(
                func.coalesce(Category.nombre, SaleItemOfferProduct.categoria_nombre) == category
            )
        
        offer_items_query = offer_items_query.group_by(SaleItem.venta_id).subquery()
        
        # PASO 4.5: Agregación de items MITAD/MITAD por venta
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
        
        # Aplicar filtro de categoría para items mitad/mitad
        if category:
            mitad_mitad_items_query = mitad_mitad_items_query.where(
                SaleItem.item_categoria == category
            )
        
        mitad_mitad_items_query = mitad_mitad_items_query.group_by(SaleItem.venta_id).subquery()
        
        # PASO 5: Unir ventas filtradas con items (directos + ofertas + mitad/mitad)
        # Nota: adjusted_fecha se usa directamente (no calculado 2 veces)
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
        
        # PASO 6: Agrupar por fecha de negocio (para promedios)
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
        
        # PASO 7: Agregación final: promedios por día de semana
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
        
        # PASO 8: Mapear resultados a días de la semana
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
        
        # Retornar ordenado: Lunes (2) a Domingo (1)
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

    async def get_balance_metrics(
        self,
        days_in_period: int = 30,
    ) -> ServiceResult:
        """
        Obtiene todas las métricas de balance del período con comparativas.
        
        Calcula:
        - Ventas totales (con MoM mes calendario)
        - Gastos totales (con MoM mes calendario)
        - Ganancia neta (ventas - gastos)
        - Margen neto ((ventas - gastos) / ventas * 100)
        
        Compara mes calendario actual (1° hasta hoy) vs mes calendario anterior (1° hasta mismo día).
        
        Args:
            days_in_period: Ignorado (mantenido por compatibilidad)
            
        Returns:
            ServiceResult con BalanceMetricsResponse
        """
        try:
            async with self.uow:
                now = datetime.now()
                
                # Período actual: 1° del mes actual hasta hoy
                current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                current_end = now
                
                # Período anterior: 1° del mes anterior hasta el mismo día del mes anterior
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
                    if prev_month == 2:
                        is_leap = (prev_year % 4 == 0 and prev_year % 100 != 0) or (prev_year % 400 == 0)
                        last_day = 29 if is_leap else 28
                    elif prev_month in [4, 6, 9, 11]:
                        last_day = 30
                    else:
                        last_day = 31
                    mom_end = datetime(prev_year, prev_month, last_day, 23, 59, 59, 999999)
                
                # Obtener ventas
                current_sales = await self._get_sales_total_between_dates(current_start, current_end)
                mom_sales = await self._get_sales_total_between_dates(mom_start, mom_end)
                
                # Obtener gastos
                current_expenses = await self._get_expenses_total_between_dates(current_start, current_end)
                mom_expenses = await self._get_expenses_total_between_dates(mom_start, mom_end)
                
                # Determinar tipo de comparación
                comparison_type = None
                previous_sales = None
                previous_expenses = None

                if mom_sales is not None and mom_sales > 0:
                    previous_sales = mom_sales
                    previous_expenses = mom_expenses
                    comparison_type = "MoM"
                
                # Calcular métricas actuales
                net_profit = current_sales - current_expenses
                margin = ((current_sales - current_expenses) / current_sales * 100) if current_sales > 0 else 0.0
                
                # Calcular métricas comparativas
                previous_net = None
                previous_margin = None
                if previous_sales is not None and previous_expenses is not None:
                    previous_net = previous_sales - previous_expenses
                    previous_margin = ((previous_sales - previous_expenses) / previous_sales * 100) if previous_sales > 0 else 0.0
                
                return ServiceResult(
                    value={
                        "sales": {
                            "current": float(current_sales or 0),
                            "previous": float(previous_sales) if previous_sales else None,
                            "comparison_type": comparison_type,
                        },
                        "expenses": {
                            "current": float(current_expenses or 0),
                            "previous": float(previous_expenses) if previous_expenses else None,
                            "comparison_type": comparison_type,
                        },
                        "net_profit": {
                            "sales": float(current_sales or 0),
                            "expenses": float(current_expenses or 0),
                            "net_profit": float(net_profit),
                            "previous_net": float(previous_net) if previous_net is not None else None,
                            "comparison_type": comparison_type,
                        },
                        "net_margin": {
                            "sales": float(current_sales or 0),
                            "expenses": float(current_expenses or 0),
                            "margin": float(margin),
                            "previous_margin": float(previous_margin) if previous_margin is not None else None,
                            "comparison_type": comparison_type,
                        },
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Error obteniendo métricas de balance: {str(e)}")
            return ServiceResult(
                error=f"Error al obtener métricas de balance: {str(e)}",
                status_code=500
            )

    async def get_monthly_balance_data(self, period: str = "monthly") -> ServiceResult:
        """
        Obtiene datos de ventas y gastos agrupados por período.

        Args:
            period: "monthly" → últimos 12 meses | "yearly" → últimos 5 años

        Returns:
            ServiceResult con MonthlyBalanceListResponse
        """
        try:
            async with self.uow:
                now = datetime.now()
                data = []

                if period == "yearly":
                    # Últimos 5 años (de más antiguo a más reciente)
                    current_year = now.year
                    for y in range(current_year - 4, current_year + 1):
                        year_start = datetime(y, 1, 1, 0, 0, 0, 0)
                        year_end   = datetime(y + 1, 1, 1, 0, 0, 0, 0)
                        year_sales    = await self._get_sales_total_between_dates(year_start, year_end)
                        year_expenses = await self._get_expenses_total_between_dates(year_start, year_end)
                        data.append({
                            "month": str(y),
                            "sales": float(year_sales or 0),
                            "expenses": float(year_expenses or 0),
                        })
                    current_month = str(current_year)
                else:
                    # Últimos 12 meses (de más antiguo a más reciente)
                    month_names = [
                        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
                    ]
                    for i in range(11, -1, -1):
                        target_date = now - timedelta(days=30 * i)
                        month_num = target_date.month
                        year_num  = target_date.year
                        month_start = datetime(year_num, month_num, 1, 0, 0, 0, 0)
                        if month_num == 12:
                            month_end = datetime(year_num + 1, 1, 1, 0, 0, 0, 0)
                        else:
                            month_end = datetime(year_num, month_num + 1, 1, 0, 0, 0, 0)
                        month_sales    = await self._get_sales_total_between_dates(month_start, month_end)
                        month_expenses = await self._get_expenses_total_between_dates(month_start, month_end)
                        data.append({
                            "month": month_names[month_num - 1],
                            "sales": float(month_sales or 0),
                            "expenses": float(month_expenses or 0),
                        })
                    current_month = month_names[now.month - 1]

                return ServiceResult(
                    value={
                        "data": data,
                        "current_month": current_month,
                    }
                )

        except Exception as e:
            self.logger.error(f"Error obteniendo datos de balance por período: {str(e)}")
            return ServiceResult(
                error=f"Error al obtener datos de balance: {str(e)}",
                status_code=500
            )

    async def _get_sales_total_between_dates(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """Obtiene el total de ventas entre dos fechas"""
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
            self.logger.error(f"Error calculando total de ventas: {str(e)}")
            return 0.0

    async def _get_expenses_total_between_dates(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """Obtiene el total de gastos entre dos fechas"""
        try:
            from app.domain.models.expense import Expense
            
            query = select(
                func.sum(Expense.monto).label("total_expenses")
            ).where(
                and_(
                    Expense.activo.is_(True),
                    Expense.fecha_pago >= start_date,
                    Expense.fecha_pago < end_date
                )
            )
            
            result = await self.uow.session.execute(query)
            row = result.scalar_one_or_none()
            
            return row if row is not None else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculando total de gastos: {str(e)}")
            return 0.0

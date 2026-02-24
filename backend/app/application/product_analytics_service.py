"""
Product Analytics Service - Análisis y rankings de productos
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
import structlog
from sqlalchemy import func, select, and_, cast, Date, union_all, text

from app.domain.models.sale import Sale
from app.domain.models.sale_item import SaleItem
from app.domain.models.sale_item_offer_product import SaleItemOfferProduct
from app.domain.models.product import Product
from app.domain.models.product_price import ProductPrice
from app.domain.models.category import Category
from app.domain.unit_of_work import AbstractUnitOfWork
from app.presentation.schemas.dashboard_schemas import FiltroTiempo


@dataclass
class ServiceResult:
    value: Optional[List | dict] = None
    error: Optional[str] = None
    status_code: int = 200


class ProductAnalyticsService:
    """Servicio especializado en análisis de productos"""
    
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        logger: structlog.BoundLogger | None = None,
    ):
        self.uow = uow
        self.logger = logger or structlog.get_logger(__name__)

    async def get_top_products(
        self,
        limit: int = 10,
        time_filter: FiltroTiempo = FiltroTiempo.HISTORICO,
        sort: str = "top",
        category: str | None = None,
    ) -> ServiceResult:
        """Obtiene los productos más/menos vendidos"""
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

    # === Métodos privados ===

    def _get_start_date_for_time_filter(self, time_filter: FiltroTiempo) -> datetime | None:
        """Calcula la fecha de inicio según el filtro de tiempo"""
        self.logger.info(f"Calculating start date for time filter: {time_filter}")
        now = datetime.now()
        
        if time_filter == FiltroTiempo.HOY:
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

    async def _get_top_products_data(
        self,
        limit: int,
        start_date: datetime | None,
        sort: str = "top",
        category: str | None = None,
    ) -> List[dict]:
        """Obtiene los productos más/menos vendidos (OPTIMIZADA)"""
        
        adjusted_fecha = Sale.fecha_creacion - text("INTERVAL '6 hours'")
        business_date_expr = cast(adjusted_fecha, Date)
        sales_filtered = select(Sale.id)
        
        if start_date is not None:
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
            sales_subq, SaleItem.venta_id == sales_subq.c.id
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
            sales_subq, SaleItem.venta_id == sales_subq.c.id
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
            sales_subq, SaleItem.venta_id == sales_subq.c.id
        ).where(
            and_(
                SaleItem.es_pizza_mitad_mitad == True,
                SaleItem.producto_id.is_(None),
                SaleItem.oferta_id.is_(None)
            )
        )
        
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

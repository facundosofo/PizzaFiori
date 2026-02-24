"""
Expense Analytics Service - Análisis de gastos
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List

import structlog
from sqlalchemy import select, func, extract, and_
from sqlalchemy.orm import aliased

from app.domain.models.expense import Expense
from app.domain.models.expense_category import ExpenseCategory
from app.domain.unit_of_work import AbstractUnitOfWork
from app.presentation.schemas.dashboard_schemas import FiltroTiempo, TipoPeriodo


@dataclass
class ServiceResult:
    value: Optional[List | dict] = None
    error: Optional[str] = None
    status_code: int = 200


class ExpenseAnalyticsService:
    """Servicio especializado en análisis de gastos"""

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        logger: structlog.BoundLogger | None = None,
    ):
        self.uow = uow
        self.logger = logger or structlog.get_logger(__name__)

    async def get_expenses_by_period(
        self,
        period: TipoPeriodo,
        limit: int = 12,
        category: str | None = None,
    ) -> ServiceResult:
        """Obtiene gastos agregados por período (mensual o anual), con filtro opcional por categoría"""
        try:
            async with self.uow:
                self.logger.info(
                    "Getting expenses by period",
                    period=period,
                    limit=limit,
                    category=category,
                )
                result = []
                
                if period == TipoPeriodo.MENSUAL:
                    result = await self._get_monthly_expenses_data(limit=limit, category=category)
                elif period == TipoPeriodo.ANUAL:
                    result = await self._get_yearly_expenses_data(limit=limit, category=category)
                
                return ServiceResult(value=result)
        except Exception as e:
            self.logger.error("Error obteniendo gastos por período", error=str(e))
            return ServiceResult(
                error=f"Error al obtener gastos por período: {str(e)}",
                status_code=500,
            )

    async def get_expenses_by_month(
        self,
        limit: int = 12,
        category: str | None = None,
    ) -> ServiceResult:
        """Obtiene gastos agregados por mes, con filtro opcional por categoría"""
        try:
            async with self.uow:
                self.logger.info(
                    "Getting expenses by month",
                    limit=limit,
                    category=category,
                )
                result = await self._get_monthly_expenses_data(limit=limit, category=category)
                return ServiceResult(value=result)
        except Exception as e:
            self.logger.error("Error obteniendo gastos por mes", error=str(e))
            return ServiceResult(
                error=f"Error al obtener gastos por mes: {str(e)}",
                status_code=500,
            )

    async def get_expenses_by_category(
        self,
        limit: int = 8,
        time_filter: FiltroTiempo = FiltroTiempo.ULTIMO_ANO,
        include_subcategories: bool = False,
    ) -> ServiceResult:
        """Obtiene gastos agregados por categoria (padres incluyen subcategorias)."""
        try:
            async with self.uow:
                self.logger.info(
                    "Getting expenses by category",
                    limit=limit,
                    time_filter=time_filter,
                    include_subcategories=include_subcategories,
                )
                
                if include_subcategories:
                    result = await self._get_expenses_by_category_with_subcategories(
                        limit=limit,
                        time_filter=time_filter,
                    )
                else:
                    result = await self._get_expenses_by_category_data(
                        limit=limit,
                        time_filter=time_filter,
                    )
                    
                return ServiceResult(value=result)
        except Exception as e:
            self.logger.error("Error obteniendo gastos por categoria", error=str(e))
            return ServiceResult(
                error=f"Error al obtener gastos por categoria: {str(e)}",
                status_code=500,
            )

    def _get_start_date_for_time_filter(
        self,
        time_filter: FiltroTiempo,
    ) -> datetime | None:
        now = datetime.now()

        if time_filter == FiltroTiempo.ULTIMO_MES:
            return now - timedelta(days=30)
        if time_filter == FiltroTiempo.ULTIMO_ANO:
            return now - timedelta(days=365)
        return None

    async def _get_monthly_expenses_data(
        self,
        limit: int,
        category: str | None,
    ) -> List[dict]:
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

        base_query = select(
            extract("year", Expense.fecha_pago).label("year"),
            extract("month", Expense.fecha_pago).label("month"),
            func.sum(Expense.monto).label("total_gastos"),
        ).select_from(
            Expense
        ).join(
            ExpenseCategory,
            Expense.categoria_gasto_id == ExpenseCategory.id,
        ).where(
            and_(
                Expense.activo.is_(True),
                Expense.fecha_pago >= start_date,
                Expense.fecha_pago < end_date,
            )
        )

        if category:
            category_result = await self.uow.session.execute(
                select(ExpenseCategory).where(
                    ExpenseCategory.nombre == category,
                    ExpenseCategory.activo.is_(True),
                )
            )
            category_row = category_result.scalars().first()

            if category_row:
                category_ids = [category_row.id]
                if category_row.padre_id is None:
                    subcategories_result = await self.uow.session.execute(
                        select(ExpenseCategory.id).where(
                            ExpenseCategory.padre_id == category_row.id,
                            ExpenseCategory.activo.is_(True),
                        )
                    )
                    category_ids.extend(subcategories_result.scalars().all())

                base_query = base_query.where(Expense.categoria_gasto_id.in_(category_ids))
            else:
                base_query = base_query.where(Expense.categoria_gasto_id.in_([]))

        query = base_query.group_by(
            "year",
            "month",
        ).order_by(
            "year",
            "month",
        )

        result = await self.uow.session.execute(query)
        rows = result.fetchall()

        months = [
            "Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
        ]

        expenses_by_month = {
            (int(row.year), int(row.month)): row
            for row in rows
        }

        results: List[dict] = []
        current_year = start_year
        current_month = start_month
        for _ in range(limit):
            row = expenses_by_month.get((current_year, current_month))
            results.append(
                {
                    "mes": f"{months[current_month - 1]} {current_year}",
                    "gastos": float(row.total_gastos or 0) if row else 0,
                }
            )

            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1

        return results

    async def _get_yearly_expenses_data(
        self,
        limit: int,
        category: str | None,
    ) -> List[dict]:
        now = datetime.now()
        start_year = now.year - (limit - 1)
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(now.year + 1, 1, 1)

        base_query = select(
            extract("year", Expense.fecha_pago).label("year"),
            func.sum(Expense.monto).label("total_gastos"),
        ).select_from(
            Expense
        ).join(
            ExpenseCategory,
            Expense.categoria_gasto_id == ExpenseCategory.id,
        ).where(
            and_(
                Expense.activo.is_(True),
                Expense.fecha_pago >= start_date,
                Expense.fecha_pago < end_date,
            )
        )

        if category:
            category_result = await self.uow.session.execute(
                select(ExpenseCategory).where(
                    ExpenseCategory.nombre == category,
                    ExpenseCategory.activo.is_(True),
                )
            )
            category_row = category_result.scalars().first()

            if category_row:
                category_ids = [category_row.id]
                if category_row.padre_id is None:
                    subcategories_result = await self.uow.session.execute(
                        select(ExpenseCategory.id).where(
                            ExpenseCategory.padre_id == category_row.id,
                            ExpenseCategory.activo.is_(True),
                        )
                    )
                    category_ids.extend(subcategories_result.scalars().all())

                base_query = base_query.where(Expense.categoria_gasto_id.in_(category_ids))
            else:
                base_query = base_query.where(Expense.categoria_gasto_id.in_([]))

        query = base_query.group_by(
            "year",
        ).order_by(
            "year",
        )

        result = await self.uow.session.execute(query)
        rows = result.fetchall()

        expenses_by_year = {
            int(row.year): row
            for row in rows
        }

        results: List[dict] = []
        for year_offset in range(limit):
            year = start_year + year_offset
            row = expenses_by_year.get(year)
            results.append(
                {
                    "año": str(year),
                    "gastos": float(row.total_gastos or 0) if row else 0,
                }
            )

        return results

    async def _get_expenses_by_category_data(
        self,
        limit: int,
        time_filter: FiltroTiempo,
    ) -> List[dict]:
        parent_category = aliased(ExpenseCategory)
        category_name = func.coalesce(parent_category.nombre, ExpenseCategory.nombre)
        start_date = self._get_start_date_for_time_filter(time_filter)

        query = select(
            category_name.label("categoria"),
            func.sum(Expense.monto).label("total_gastos"),
        ).select_from(
            Expense
        ).join(
            ExpenseCategory,
            Expense.categoria_gasto_id == ExpenseCategory.id,
        ).outerjoin(
            parent_category,
            ExpenseCategory.padre_id == parent_category.id,
        ).where(
            Expense.activo.is_(True)
        )

        if start_date is not None:
            query = query.where(Expense.fecha_pago >= start_date)

        query = query.group_by(
            category_name
        ).order_by(
            func.sum(Expense.monto).desc()
        ).limit(limit)

        result = await self.uow.session.execute(query)
        rows = result.fetchall()

        return [
            {
                "categoria": row.categoria or "Sin categoria",
                "gastos": float(row.total_gastos or 0),
            }
            for row in rows
        ]

    async def _get_expenses_by_category_with_subcategories(
        self,
        limit: int,
        time_filter: FiltroTiempo,
    ) -> List[dict]:
        """Obtiene gastos por categoría con subcategorías anidadas."""
        start_date = self._get_start_date_for_time_filter(time_filter)
        
        # Obtener todas las categorías padre activas
        parent_categories_query = select(
            ExpenseCategory.id,
            ExpenseCategory.nombre,
        ).where(
            and_(
                ExpenseCategory.padre_id.is_(None),
                ExpenseCategory.activo.is_(True),
            )
        )
        
        parent_categories_result = await self.uow.session.execute(parent_categories_query)
        parent_categories = parent_categories_result.fetchall()
        
        results = []
        for parent_cat in parent_categories:
            # Obtener IDs de la categoría y sus subcategorías
            category_ids = [parent_cat.id]
            
            # Obtener subcategorías
            subcategories_query = select(ExpenseCategory.id, ExpenseCategory.nombre).where(
                and_(
                    ExpenseCategory.padre_id == parent_cat.id,
                    ExpenseCategory.activo.is_(True),
                )
            )
            subcategories_result = await self.uow.session.execute(subcategories_query)
            subcategories_rows = subcategories_result.fetchall()
            
            # Calcular total de gastos para la categoría padre (incluyendo subcategorías)
            all_category_ids = [parent_cat.id] + [row.id for row in subcategories_rows]
            
            total_query = select(
                func.sum(Expense.monto).label("total_gastos"),
            ).where(
                and_(
                    Expense.activo.is_(True),
                    Expense.categoria_gasto_id.in_(all_category_ids),
                )
            )
            
            if start_date is not None:
                total_query = total_query.where(Expense.fecha_pago >= start_date)
            
            total_result = await self.uow.session.execute(total_query)
            total_row = total_result.fetchone()
            total_gastos = float(total_row.total_gastos or 0) if total_row else 0
            
            # Solo incluir categorías con gastos > 0
            if total_gastos > 0:
                # Obtener desglose de subcategorías
                subcategories_detail = []
                for subcat_row in subcategories_rows:
                    subcat_query = select(
                        func.sum(Expense.monto).label("total_gastos"),
                    ).where(
                        and_(
                            Expense.activo.is_(True),
                            Expense.categoria_gasto_id == subcat_row.id,
                        )
                    )
                    
                    if start_date is not None:
                        subcat_query = subcat_query.where(Expense.fecha_pago >= start_date)
                    
                    subcat_result = await self.uow.session.execute(subcat_query)
                    subcat_total = subcat_result.fetchone()
                    
                    if subcat_total and subcat_total.total_gastos and float(subcat_total.total_gastos) > 0:
                        subcategories_detail.append({
                            "categoria": subcat_row.nombre,
                            "gastos": float(subcat_total.total_gastos),
                        })
                
                # Ordenar subcategorías por gastos descendente
                subcategories_detail.sort(key=lambda x: x["gastos"], reverse=True)
                
                results.append({
                    "categoria": parent_cat.nombre or "Sin categoría",
                    "gastos": total_gastos,
                    "subcategorias": subcategories_detail if subcategories_detail else None,
                })
        
        # Ordenar por gastos totales descendente y limitar
        results.sort(key=lambda x: x["gastos"], reverse=True)
        return results[:limit]

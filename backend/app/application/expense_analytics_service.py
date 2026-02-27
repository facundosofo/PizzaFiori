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

    async def get_expenses_summary(self) -> ServiceResult:
        """Obtiene resumen de gastos para cards del dashboard con comparaciones de períodos equivalentes."""
        try:
            async with self.uow:
                now = datetime.now()
                
                # MTD (Month To Date): Comparar febrero 1-25 vs enero 1-25
                mtd_current = self._get_mtd_range(now)
                mtd_previous = self._get_previous_month_equivalent(now)
                
                # YTD (Year To Date): Comparar 2026 ene 1 - feb 25 vs 2025 ene 1 - feb 25
                ytd_current = self._get_ytd_range(now)
                ytd_previous = self._get_previous_year_equivalent(now)
                
                # Gastos MTD y YTD
                monthly_total = await self._get_total_expenses_between(mtd_current[0], mtd_current[1])
                prev_month_total = await self._get_total_expenses_between(mtd_previous[0], mtd_previous[1])
                yearly_total = await self._get_total_expenses_between(ytd_current[0], ytd_current[1])
                prev_year_total = await self._get_total_expenses_between(ytd_previous[0], ytd_previous[1])

                monthly_change = self._calculate_variation_pct(monthly_total, prev_month_total)
                yearly_change = self._calculate_variation_pct(yearly_total, prev_year_total)

                # Categoría con mayor crecimiento (último mes completo vs mes anterior)
                last_month = self._get_previous_complete_month(now)
                current_by_category = await self._get_category_totals_between(mtd_current[0], mtd_current[1])
                prev_by_category = await self._get_category_totals_between(mtd_previous[0], mtd_previous[1])
                top_growth = self._get_top_growth_category(current_by_category, prev_by_category)

                # Obtener nombres de períodos para la respuesta
                month_names = [
                    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
                ]
                comparacion_mes = month_names[mtd_previous[0].month - 1]
                comparacion_ano = ytd_previous[0].year

                return ServiceResult(
                    value={
                        "resultado_mensual": float(monthly_total),
                        "variacion_mensual_pct": monthly_change,
                        "comparacion_mes": comparacion_mes,
                        "resultado_anual": float(yearly_total),
                        "variacion_anual_pct": yearly_change,
                        "comparacion_ano": comparacion_ano,
                        "categoria_mayor_crecimiento": top_growth,
                    }
                )
        except Exception as e:
            self.logger.error("Error obteniendo resumen de gastos", error=str(e))
            return ServiceResult(
                error=f"Error al obtener resumen de gastos: {str(e)}",
                status_code=500,
            )

    def _get_mtd_range(self, date: datetime) -> tuple[datetime, datetime]:
        """Retorna (1° del mes actual, fecha actual) para MTD."""
        start = datetime(date.year, date.month, 1)
        return (start, date)

    def _get_ytd_range(self, date: datetime) -> tuple[datetime, datetime]:
        """Retorna (1° enero año actual, fecha actual) para YTD."""
        start = datetime(date.year, 1, 1)
        return (start, date)

    def _get_previous_month_equivalent(self, date: datetime) -> tuple[datetime, datetime]:
        """Retorna el rango equivalente del mes anterior (mismo día).
        
        Ej: si hoy es 25 de febrero, retorna (1 enero, 25 enero)
        """
        # Restar un mes
        if date.month == 1:
            prev_year = date.year - 1
            prev_month = 12
        else:
            prev_year = date.year
            prev_month = date.month - 1
        
        start = datetime(prev_year, prev_month, 1)
        
        # Si el mes anterior tiene menos días que el día actual, usar último día del mes anterior
        try:
            end = datetime(prev_year, prev_month, date.day)
        except ValueError:
            # Mes anterior no tiene ese día (ej: 31 enero -> 28/29 febrero)
            if prev_month == 2:
                # Febrero: buscar último día
                end = datetime(prev_year, 3, 1) - timedelta(days=1)
            else:
                # Otros meses
                end = datetime(prev_year, prev_month + 1, 1) - timedelta(days=1)
        
        return (start, end)

    def _get_previous_year_equivalent(self, date: datetime) -> tuple[datetime, datetime]:
        """Retorna el rango equivalente del año anterior (mismo día del mismo mes).
        
        Ej: si hoy es 25 febrero 2026, retorna (1 enero 2025, 25 febrero 2025)
        """
        start = datetime(date.year - 1, 1, 1)
        
        try:
            end = datetime(date.year - 1, date.month, date.day)
        except ValueError:
            # Año anterior no tiene ese día (ej: 29 feb 2024 -> 28 feb 2023)
            if date.month == 2:
                end = datetime(date.year - 1, 3, 1) - timedelta(days=1)
            else:
                end = datetime(date.year - 1, date.month + 1, 1) - timedelta(days=1)
        
        return (start, end)

    def _get_previous_complete_month(self, date: datetime) -> tuple[datetime, datetime]:
        """Retorna el mes completo anterior.
        
        Ej: si hoy es 25 febrero, retorna (1 enero, 31 enero)
        """
        if date.month == 1:
            prev_year = date.year - 1
            prev_month = 12
        else:
            prev_year = date.year
            prev_month = date.month - 1
        
        start = datetime(prev_year, prev_month, 1)
        # Último día del mes anterior
        if prev_month == 12:
            end = datetime(prev_year + 1, 1, 1) - timedelta(days=1)
        else:
            end = datetime(prev_year, prev_month + 1, 1) - timedelta(days=1)
        
        return (start, end)

    def _calculate_variation_pct(self, current: float, previous: float) -> float | None:
        if previous == 0:
            if current == 0:
                return 0.0
            return None
        return ((current - previous) / previous) * 100

    async def _get_total_expenses_between(self, start_date: datetime, end_date: datetime) -> float:
        query = select(func.coalesce(func.sum(Expense.monto), 0)).select_from(
            Expense
        ).join(
            ExpenseCategory,
            Expense.categoria_gasto_id == ExpenseCategory.id,
        ).where(
            and_(
                Expense.activo.is_(True),
                ExpenseCategory.activo.is_(True),
                Expense.fecha_pago >= start_date,
                Expense.fecha_pago < end_date,
            )
        )

        result = await self.uow.session.execute(query)
        return float(result.scalar() or 0)

    async def _get_category_totals_between(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, float]:
        query = select(
            ExpenseCategory.nombre,
            func.coalesce(func.sum(Expense.monto), 0).label("total_gastos"),
        ).select_from(
            Expense
        ).join(
            ExpenseCategory,
            Expense.categoria_gasto_id == ExpenseCategory.id,
        ).where(
            and_(
                Expense.activo.is_(True),
                ExpenseCategory.activo.is_(True),
                Expense.fecha_pago >= start_date,
                Expense.fecha_pago < end_date,
            )
        ).group_by(ExpenseCategory.nombre)

        result = await self.uow.session.execute(query)
        rows = result.fetchall()
        return {row.nombre: float(row.total_gastos or 0) for row in rows}

    def _get_top_growth_category(
        self,
        current: dict[str, float],
        previous: dict[str, float],
    ) -> dict | None:
        if not current and not previous:
            return None

        categories = set(current.keys()) | set(previous.keys())
        best_category = None
        best_change = None
        best_is_comparable = False

        for category in categories:
            current_total = current.get(category, 0.0)
            previous_total = previous.get(category, 0.0)
            if current_total == 0 and previous_total == 0:
                continue

            change_pct = self._calculate_variation_pct(current_total, previous_total)
            is_comparable = change_pct is not None

            if best_category is None:
                best_category = category
                best_change = change_pct
                best_is_comparable = is_comparable
                continue

            if is_comparable and not best_is_comparable:
                best_category = category
                best_change = change_pct
                best_is_comparable = True
                continue

            if is_comparable and best_is_comparable and change_pct is not None and best_change is not None:
                if change_pct > best_change:
                    best_category = category
                    best_change = change_pct
                continue

            if not is_comparable and not best_is_comparable:
                if current_total > (current.get(best_category, 0.0) if best_category else 0.0):
                    best_category = category
                    best_change = change_pct

        if not best_category:
            return None

        return {
            "categoria": best_category,
            "porcentaje": best_change,
        }

    def _get_start_date_for_time_filter(
        self,
        time_filter: FiltroTiempo,
    ) -> datetime | None:
        """Calcula la fecha de inicio según el filtro de tiempo (períodos calendario)."""
        from app.application.analytics_utils import get_start_date_for_time_filter
        result = get_start_date_for_time_filter(time_filter)
        self.logger.info(f"Filter {time_filter} → start_date: {result}")
        return result

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

    async def get_total_expenses_with_comparison(
        self,
        days_in_period: int = 30,
    ) -> ServiceResult:
        """
        Obtiene el total de gastos del período actual con comparativa.
        
        Compara mes calendario actual (1° hasta hoy) vs mes calendario anterior (1° hasta mismo día).
        
        Args:
            days_in_period: Ignorado (mantenido por compatibilidad)
            
        Returns:
            ServiceResult con TotalExpensesKPIResponse
        """
        try:
            async with self.uow:
                now = datetime.now()
                
                # Período actual: 1° del mes actual hasta hoy
                current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                current_end = now
                
                # Obtener gastos del período actual
                current_total = await self._get_expenses_total_between_dates(current_start, current_end)

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
                
                mom_total = await self._get_expenses_total_between_dates(mom_start, mom_end)

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
            self.logger.error(f"Error obteniendo total de gastos con comparativa: {str(e)}")
            return ServiceResult(
                error=f"Error al obtener total de gastos: {str(e)}",
                status_code=500
            )

    async def _get_expenses_total_between_dates(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> float | None:
        """
        Obtiene el total de gastos entre dos fechas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Total de gastos en pesos, o None si no hay datos
        """
        try:
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
            self.logger.error(f"Error calculando total de gastos entre {start_date} y {end_date}: {str(e)}")
            return None

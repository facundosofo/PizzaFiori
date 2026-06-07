"""
analytics_utils.py — Utilidades compartidas para módulos de análisis

Lógica canónica de filtros temporales:
  - ULTIMO_MES  → 1° del mes calendario actual hasta hoy
  - ULTIMO_ANO  → 1° de enero del año actual hasta hoy
  - HOY         → desde las 00:00 de hoy
  - ULTIMOS_7_DIAS → desde las 00:00 de hace 6 días (7 días completos incl. hoy)
  - HISTORICO   → sin límite de fecha (None)
"""

from datetime import datetime, timedelta

from app.presentation.schemas.dashboard_schemas import FiltroTiempo


def get_start_date_for_time_filter(time_filter: FiltroTiempo) -> datetime | None:
    """
    Calcula la fecha de inicio según el filtro de tiempo.

    Todos los filtros se anclan a períodos calendario, no rolling:
      - ULTIMO_MES  → 1° del mes actual a las 00:00
      - ULTIMO_ANO  → 1° de enero del año actual a las 00:00
      - HOY         → hoy a las 00:00
      - ULTIMOS_7_DIAS → hace 6 días a las 00:00 (7 días completos incl. hoy)
      - HISTORICO   → None (sin filtro)

    El ajuste de horario de negocio (-6 h) se aplica en las queries SQL,
    no en este método.

    Returns:
        datetime | None: Fecha de inicio, None para histórico (sin filtro).
    """
    now = datetime.now()

    if time_filter == FiltroTiempo.HOY:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    if time_filter == FiltroTiempo.ULTIMOS_7_DIAS:
        return (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)

    if time_filter == FiltroTiempo.ULTIMO_MES:
        # Primer día del mes calendario actual
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if time_filter == FiltroTiempo.ULTIMO_ANO:
        # Primer día del año calendario actual (1° de enero)
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # HISTORICO — sin límite de fecha
    return None

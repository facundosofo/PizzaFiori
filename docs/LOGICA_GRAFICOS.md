# Lógica de Gráficos — Dashboard PizzaFiori

> Documento de referencia técnica sobre qué datos consume cada gráfico, cómo se filtran y cuál es el período real que representan.

---

## Índice

1. [Filtros temporales](#1-filtros-temporales)
2. [KPI Cards](#2-kpi-cards)
3. [Gráficos de Ventas](#3-gráficos-de-ventas)
4. [Gráficos de Gastos](#4-gráficos-de-gastos)
5. [Gráficos de Balance](#5-gráficos-de-balance)
6. [Tab General — resumen de gráficos](#6-tab-general--resumen-de-gráficos)
7. [Notas de implementación](#7-notas-de-implementación)

---

## 1. Filtros temporales

### 1.1 Opciones disponibles en la UI

El selector `TimeFilterSelector` ofrece **tres opciones** en todos los gráficos del dashboard:

| Valor | Label | Descripción visible | Período real (backend) |
|---|---|---|---|
| `last_month` | Mes actual | Del 1° del mes hasta hoy | `now.replace(day=1, hour=0, minute=0, second=0)` |
| `last_year` | Año actual | Del 1° de enero hasta hoy | `now.replace(month=1, day=1, hour=0, minute=0, second=0)` |
| `all_time` | Histórico | Todos los datos | Sin filtro de fecha (`NULL`) |

> Las opciones `Hoy` y `Últimos 7 días` fueron eliminadas de la UI. Sus valores (`today`, `last_7_days`) siguen existiendo en el enum del backend pero no se exponen al usuario.

### 1.2 Lógica canónica centralizada

Todos los servicios (Dashboard, Ventas, Productos, Gastos) delegan el cálculo de fechas a **`analytics_utils.get_start_date_for_time_filter()`**, definida en `backend/app/application/analytics_utils.py`. No existe duplicación.

```python
# analytics_utils.py — lógica canónica
def get_start_date_for_time_filter(time_filter: FiltroTiempo) -> datetime | None:
    now = datetime.now()
    match time_filter:
        case FiltroTiempo.HOY:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        case FiltroTiempo.ULTIMOS_7_DIAS:
            return (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        case FiltroTiempo.ULTIMO_MES:
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        case FiltroTiempo.ULTIMO_ANO:
            return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        case FiltroTiempo.HISTORICO:
            return None
```

### 1.3 Ajuste por horario de negocio

Las queries de ventas aplican un ajuste de **`−6 horas`** sobre `fecha_creacion` para que el "día de negocio" (16:00 a 06:00) coincida con el día calendario. Este ajuste lo aplica directamente la query SQL y **no está incluido** en `get_start_date_for_time_filter`.

---

## 2. KPI Cards

### 2.1 `TotalSalesKPICard` — Ventas Totales

| Atributo | Detalle |
|---|---|
| **Endpoint** | `GET /api/dashboard/sales/total` |
| **Servicio** | `SalesAnalyticsService.get_total_sales_with_comparison()` |
| **Período actual** | Del **1° del mes calendario actual** hasta hoy |
| **Período comparación** | **Mes anterior completo** (día 1 hasta último día del mes anterior, MoM) |
| **Label comparación** | Muestra el nombre real del mes anterior (ej: "vs Febrero"), calculado en el frontend |

---

### 2.2 `TotalExpensesKPICard` — Gastos Totales

| Atributo | Detalle |
|---|---|
| **Endpoint** | `GET /api/dashboard/expenses/total` |
| **Servicio** | `ExpenseAnalyticsService.get_total_expenses_with_comparison()` |
| **Período actual** | Del **1° del mes calendario actual** hasta hoy |
| **Período comparación** | **Mes anterior completo** (día 1 hasta último día del mes anterior, MoM) |
| **Label comparación** | Muestra el nombre real del mes anterior (ej: "vs Febrero"), calculado en el frontend |

---

### 2.3 `NetProfitKPICard` — Resultado Neto

| Atributo | Detalle |
|---|---|
| **Fuente de datos** | Recibe `BalanceMetrics.net_profit` desde el componente padre |
| **Período** | Mes calendario actual (1° hasta hoy) |
| **Período comparación** | **Mes anterior completo** (MoM) |
| **Cálculo** | `ventas − gastos` del período (resultado neto) |
| **Label comparación** | Muestra el nombre real del mes anterior (ej: "vs Febrero") |

---

### 2.4 `NetMarginKPICard` — Margen Neto

| Atributo | Detalle |
|---|---|
| **Fuente de datos** | Recibe `BalanceMetrics.net_margin` desde el componente padre |
| **Período** | Mes calendario actual (1° hasta hoy) |
| **Período comparación** | **Mes anterior completo** (MoM) |
| **Cálculo** | `(ventas − gastos) / ventas × 100` |
| **Label comparación** | Muestra el nombre real del mes anterior (ej: "vs Febrero") |

---

### 2.5 `TotalOrdersKPICard` — Total de Pedidos

| Atributo | Detalle |
|---|---|
| **Fuente de datos** | Recibe `monthlyRevenue` (últimos 12 meses) — no hace llamada propia |
| **Período mostrado** | Suma de pedidos del mes actual dentro del array mensual |
| **Label comparación** | Muestra el nombre real del mes anterior (ej: "vs Febrero") |

---

### 2.6 Cards de resumen de Gastos (Tab Gastos)

Las tres cards del tab Gastos (`Resultado mensual`, `Resultado anual`, `Categoría que más creció`) consumen `GET /api/dashboard/expenses/summary` → `ExpenseAnalyticsService.get_expenses_summary()`.

| Card | Período actual | Período comparación |
|---|---|---|
| **Resultado mensual** | MTD: 1° del mes actual hasta hoy | **Mes anterior completo** (día 1 hasta último día) |
| **Resultado anual** | YTD: 1° de enero hasta hoy | **Año anterior completo** (1° enero – 31 dic del año anterior) |
| **Categoría que más creció** | MTD por categoría | Mes anterior completo por categoría |

El label de comparación viene directamente del backend (`comparacion_mes`, `comparacion_ano`) y muestra el nombre del mes/año real (ej: "vs Febrero", "vs 2025").

---

## 3. Gráficos de Ventas

### 3.1 `RevenueChart` — Ventas por Período

**Ubicación**: Tab **Ventas**

| Período | Endpoint | Parámetros | Descripción |
|---|---|---|---|
| **Diario** | `GET /api/dashboard/revenue?period=daily&limit=30` | `limit=30` | **30 días rolling** desde el backend. El frontend genera los últimos 30 días desde hoy (cliente), cruzando con los datos del backend por fecha y llenando con `0` los días sin datos. |
| **Mensual** | `GET /api/dashboard/revenue?period=monthly&limit=12` | `limit=12` | Últimos **12 meses** calendario |
| **Anual** | `GET /api/dashboard/revenue?period=yearly&limit=5` | `limit=5` | Últimos **5 años** |

**Métricas seleccionables**: Ingresos ($) / Pedidos (cantidad) / Items (unidades)
**Tipos de gráfico**: Área (default) / Barras
**Estado inicial**: Período mensual, métrica ingresos

> **Nota sobre modo diario**: El `RevenueChart` en modo diario usa intencionalmente una ventana rolling de 30 días (no el mes calendario), para que siempre muestre exactamente 30 puntos en el eje X independientemente del día del mes. Es un gráfico de tendencia, no de resumen de período.

---

### 3.2 `SalesByCategoryChart` — Ventas por Categoría

**Ubicación**: Tab **Ventas** y Tab **General**
**Componente**: Pie chart
**Endpoint**: `GET /api/dashboard/sales-by-category?limit=8&time_filter={filter}`

| Filtro | Período real |
|---|---|
| `last_month` (default en Tab General) | Del 1° del mes hasta hoy |
| `last_year` | Del 1° de enero hasta hoy |
| `all_time` | Todos los datos |

---

### 3.3 `WeekdayChart` — Promedio de Ventas por Día de Semana

**Endpoint**: `GET /api/dashboard/revenue/weekday?category={cat}&time_filter={filter}`

| Ubicación | Estado | Filtro tiempo default | Categoría |
|---|---|---|---|
| **Tab Ventas** | `weekdayData` (controlado por `weekdayTimeFilter` + `weekdayCategory`) | `last_month` | Seleccionable |
| **Tab General** | `generalWeekdayData` (independiente, fijo) | `last_month` | Sin filtro (todas) |

**Métricas**: Ingresos / Pedidos / Items
**Datos**: Promedio por día de semana (Lunes–Domingo) calculado sobre el período elegido

> Los dos gráficos son **completamente independientes**. Cambiar el filtro en Tab Ventas no afecta al gráfico de Tab General.

---

### 3.4 `TopProductsTable` — Top Productos

**Endpoint**: `GET /api/dashboard/products/top?limit={n}&sort={top|bottom}&time_filter={filter}&category={cat}`

| Filtro | Opciones |
|---|---|
| Período | Mes actual / Año actual / Histórico |
| Ordenamiento | Top (más vendidos, default) / Bottom (menos vendidos) |
| Categoría | Todas / filtrables por categoría del producto |
| Límite | 5 (default), configurable |

---

## 4. Gráficos de Gastos

### 4.1 `ExpenseByMonthChart` — Gastos por Período

**Ubicación**: Tab **Gastos**
**Endpoint**: `GET /api/dashboard/expenses?period={period}&limit={limit}&category={cat}`

| Período | Límite | Descripción |
|---|---|---|
| Mensual (default) | 12 | Últimos **12 meses** |
| Anual | 5 | Últimos **5 años** |

**Tipos de gráfico**: Área (default) / Barras
**Filtro por categoría de gasto**: Sí

> El backend devuelve los datos ordenados del más antiguo al más reciente. No usa `time_filter` — el `limit` define cuántos períodos hacia atrás se muestran.

---

### 4.2 `ExpenseByCategoryChart` — Gastos por Categoría

**Ubicación**: Tab **Gastos** y Tab **General**
**Componente**: Pie chart con detalle expandible de subcategorías
**Endpoint**: `GET /api/dashboard/expenses/by-category?limit=8&time_filter={filter}&include_subcategories=true`

| Filtro disponible | Valor | Período real |
|---|---|---|
| Mes actual (default) | `last_month` | Del 1° del mes hasta hoy |
| Año actual | `last_year` | Del 1° de enero hasta hoy |

---

## 5. Gráficos de Balance

### 5.1 `MonthlyBalanceBarChart` — Resultado Neto

**Ubicación**: Tab **Balance** y Tab **General**
**Endpoint**: `GET /api/dashboard/balance/monthly?period={period}`
**Servicio**: `DashboardService.get_monthly_balance_data()`

| Período | Datos devueltos |
|---|---|
| Mensual (default) | Últimos **12 meses** calendario (mes por mes) |
| Anual | Últimos **5 años** (año por año) |

Muestra dos barras por período (Ventas en verde, Gastos en rojo). El mes/año actual se resalta.

> Las instancias de Tab General y Tab Balance son independientes (`generalBalancePeriod` vs `balancePeriod`), ambas iniciadas en `'monthly'`.

---

### 5.2 `NetMarginLineChart` — Evolución del Margen Neto

**Ubicación**: Tab **Balance** (junto a `MonthlyBalanceBarChart`)
**Fuente de datos**: Mismo conjunto que `MonthlyBalanceBarChart` (`monthlyBalanceData`)
**Cálculo**: `(ventas − gastos) / ventas × 100` por cada período

El área y la línea cambian de color según el signo del margen:
- **Verde** (`#16a34a`) → margen positivo (ganancia)
- **Rojo** (`#ef4444`) → margen negativo (pérdida)

El eje Y arranca desde `0%` cuando no hay meses negativos, para mantener consistencia visual con los demás gráficos. Si hay meses negativos, el dominio se extiende hacia abajo con padding automático.

> El `NetMarginLineChart` no tiene filtro propio — siempre refleja el mismo `balancePeriod` que `MonthlyBalanceBarChart`.

---

## 6. Tab General — resumen de gráficos

El Tab General combina gráficos reducidos de todas las tabs. Todos los estados son **independientes**:

| Gráfico | Estado | Filtro tiempo default | ¿Comparte estado con otra tab? |
|---|---|---|---|
| `WeekdayChart` | `generalWeekdayData` | `last_month` (fijo) | ❌ No |
| `MonthlyBalanceBarChart` | `generalBalanceData` | Mensual (12 meses) | ❌ No |
| KPI Cards | — | Mes calendario actual | ❌ No |
| `SalesByCategoryChart` | `generalSalesByCategory` | `last_month` | ❌ No |
| `ExpenseByCategoryChart` | `generalExpensesByCategory` | `last_month` | ❌ No |
| `TopProductsTable` | `generalTopProducts` | `last_month` | ❌ No |

---

## 7. Notas de implementación

### 7.1 `RevenueChart` diario — ventana rolling intencional

El gráfico diario de ventas usa una ventana rolling de 30 días tanto en el backend (`limit=30`) como en el frontend (genera los últimos 30 días desde `new Date()`). Esto es **intencional**: el gráfico de tendencia diario siempre muestra exactamente 30 puntos en el eje X, lo que da una vista de tendencia estable independientemente del día del mes. No está alineado al mes calendario, a diferencia de los KPI Cards.

### 7.2 `getBalanceMetrics` — endpoint sin parámetros

`GET /api/dashboard/balance` no acepta parámetros de período. El backend siempre calcula el mes calendario actual (1° hasta hoy) y lo compara contra el **mes anterior completo** (día 1 hasta último día del mes pasado). El frontend no envía ningún parámetro.

### 7.3 Aritmética de meses en `get_monthly_balance_data`

El loop de 12 meses usa aritmética de calendario real en lugar de `timedelta(days=30 * i)`. Esto evita que meses de diferente longitud generen duplicados o saltos en el eje X (ej: enero apareciendo dos veces cuando el mes tiene 31 días). La fórmula correcta:

```python
month_offset = now.month - 1 - i
year_num  = now.year + month_offset // 12
month_num = month_offset % 12 + 1
```

Un set `seen_months` defensivo descarta cualquier duplicado residual antes de retornar los datos.

---

## Resumen de períodos por gráfico

```
Gráfico                            | Período efectivo
-----------------------------------|--------------------------------------------------
KPI Ventas / Gastos / Balance      | Mes calendario actual (1°/MM hasta hoy)
RevenueChart - diario              | Rolling 30 días desde el cliente (intencional)
RevenueChart - mensual             | Últimos 12 meses (limit backend)
RevenueChart - anual               | Últimos 5 años (limit backend)
WeekdayChart (Tab Ventas)          | Configurable: mes actual / año actual / histórico
WeekdayChart (Tab General)         | Mes calendario actual fijo, todas las categorías
SalesByCategoryChart               | Configurable: mes actual / año actual / histórico
TopProductsTable                   | Configurable: mes actual / año actual / histórico
ExpenseByMonthChart                | Últimos 12 meses / 5 años (limit, sin time_filter)
ExpenseByCategoryChart             | Configurable: mes actual / año actual
MonthlyBalanceBarChart             | Últimos 12 meses / 5 años (period param)
NetMarginLineChart                 | Mismos datos que MonthlyBalanceBarChart
```

# Benchmarks - PizzaFiori

Documentación completa de la suite de benchmarks de repositorios del proyecto PizzaFiori.

## 📊 Resumen de Benchmarks

**Estado Actual:**
- ✅ **51 benchmarks pasando al 100%**
- ⚡ Tiempo total de ejecución: ~14 segundos
- 🔁 Configuración: `rounds=50, iterations=3, warmup_rounds=3`

### Distribución por Módulo

| Módulo | Benchmarks | Archivo |
|--------|:----------:|---------|
| **Products + Categories** | 10 | `bench_db_products.py` |
| **Sales** | 8 | `bench_db_sales.py` |
| **Expenses + Offers** | 13 | `bench_db_expenses.py` |
| **Users** | 7 | `bench_db_users.py` |
| **Stock + Sequences** | 4 | `bench_db_stock.py` |
| **Audit Log** | 9 | `bench_db_audit.py` |
| **TOTAL** | **51** | **6 archivos** |

## 🏎️ Resultados de Referencia

Medidos en **Windows 11 / Intel i5-12600K / PostgreSQL 16 / Python 3.14.2**.

> Los valores se expresan en **microsegundos (µs)**. Menor es mejor.

### Niveles de Latencia

| Tier | Rango | Descripción |
|------|-------|-------------|
| 🟢 Tier 1 | < 600 µs | COUNT y PK lookup por índice único |
| 🟢 Tier 2 | 600 – 900 µs | Lista simple / filtro por campo indexado |
| 🟡 Tier 3 | 900 µs – 1.3 ms | Filtros combinados o JOIN simple |
| 🟡 Tier 4 | 1.3 – 2.0 ms | Paginación con OFFSET o selectinload 1-nivel |
| 🔴 Tier 5 | 2.0 – 3.5 ms | Selectinload multi-nivel (ventas con ítems) |
| 🔴 Tier 6 | > 3.5 ms | SELECT FOR UPDATE / queries muy amplias |

### Tabla Completa de Resultados

| Benchmark | Mean (µs) | Min (µs) | Max (µs) | StdDev | Tier |
|-----------|----------:|---------:|---------:|-------:|:----:|
| `bench_db_product_category_list_all` | 520 | 490 | 610 | 18 | 🟢 |
| `bench_db_product_category_list_active` | 530 | 500 | 620 | 20 | 🟢 |
| `bench_db_product_category_get_by_id` | 510 | 480 | 580 | 15 | 🟢 |
| `bench_db_product_list_all` | 820 | 760 | 950 | 35 | 🟢 |
| `bench_db_product_list_active` | 840 | 780 | 970 | 38 | 🟢 |
| `bench_db_product_list_by_category` | 740 | 700 | 860 | 30 | 🟢 |
| `bench_db_product_get_by_id` | 550 | 510 | 640 | 22 | 🟢 |
| `bench_db_product_get_by_ids_5` | 680 | 630 | 790 | 28 | 🟢 |
| `bench_db_product_get_by_ids_all` | 920 | 860 | 1080 | 42 | 🟡 |
| `bench_db_product_count` | 490 | 460 | 560 | 14 | 🟢 |
| `bench_db_sale_list_20` | 2350 | 2100 | 2900 | 150 | 🔴 |
| `bench_db_sale_list_50` | 3100 | 2800 | 3800 | 200 | 🔴 |
| `bench_db_sale_list_paginated_offset` | 2400 | 2150 | 2950 | 160 | 🔴 |
| `bench_db_sale_list_with_date_filter_30d` | 2200 | 1950 | 2700 | 140 | 🔴 |
| `bench_db_sale_get_by_id` | 1450 | 1300 | 1750 | 80 | 🟡 |
| `bench_db_sale_count` | 490 | 460 | 560 | 13 | 🟢 |
| `bench_db_sale_count_with_date_filter` | 580 | 540 | 670 | 20 | 🟢 |
| `bench_db_sale_get_distinct_years` | 540 | 500 | 630 | 17 | 🟢 |
| `bench_db_expense_list_all` | 720 | 670 | 840 | 28 | 🟢 |
| `bench_db_expense_list_by_category` | 650 | 600 | 750 | 24 | 🟢 |
| `bench_db_expense_list_by_date_30d` | 710 | 660 | 830 | 26 | 🟢 |
| `bench_db_expense_list_by_date_and_category` | 730 | 680 | 850 | 30 | 🟢 |
| `bench_db_expense_get_by_id` | 520 | 490 | 600 | 16 | 🟢 |
| `bench_db_expense_count` | 480 | 450 | 550 | 12 | 🟢 |
| `bench_db_expense_category_list_all` | 560 | 520 | 650 | 18 | 🟢 |
| `bench_db_expense_category_list_active` | 570 | 530 | 660 | 19 | 🟢 |
| `bench_db_expense_category_get_roots` | 500 | 470 | 580 | 14 | 🟢 |
| `bench_db_expense_category_get_children` | 510 | 480 | 590 | 15 | 🟢 |
| `bench_db_offer_list_all` | 1050 | 960 | 1250 | 55 | 🟡 |
| `bench_db_offer_list_active` | 1080 | 990 | 1280 | 58 | 🟡 |
| `bench_db_offer_get_by_id` | 870 | 800 | 1020 | 40 | 🟢 |
| `bench_db_user_list_all` | 650 | 610 | 750 | 22 | 🟢 |
| `bench_db_user_list_by_role_admin` | 600 | 560 | 690 | 20 | 🟢 |
| `bench_db_user_list_by_role_user` | 620 | 580 | 720 | 21 | 🟢 |
| `bench_db_user_get_by_id` | 510 | 480 | 590 | 14 | 🟢 |
| `bench_db_user_get_by_username` | 520 | 490 | 600 | 16 | 🟢 |
| `bench_db_user_get_by_email` | 520 | 490 | 600 | 15 | 🟢 |
| `bench_db_user_count` | 480 | 450 | 550 | 12 | 🟢 |
| `bench_db_stock_get_all` | 540 | 500 | 630 | 18 | 🟢 |
| `bench_db_stock_get_by_categoria_id` | 500 | 470 | 580 | 14 | 🟢 |
| `bench_db_sequence_get_for_update_today` | 4200 | 3800 | 5200 | 280 | 🔴 |
| `bench_db_sequence_get_for_update_yesterday` | 4100 | 3700 | 5100 | 270 | 🔴 |
| `bench_db_audit_get_by_date_range_10d` | 850 | 790 | 990 | 38 | 🟢 |
| `bench_db_audit_get_by_date_range_entity_filter` | 880 | 820 | 1030 | 40 | 🟢 |
| `bench_db_audit_get_by_date_range_username_filter` | 900 | 840 | 1050 | 42 | 🟡 |
| `bench_db_audit_get_by_date_range_action_filter` | 890 | 830 | 1040 | 41 | 🟡 |
| `bench_db_audit_get_by_entity` | 580 | 540 | 670 | 18 | 🟢 |
| `bench_db_audit_get_by_id` | 510 | 480 | 590 | 14 | 🟢 |
| `bench_db_audit_count` | 480 | 450 | 550 | 12 | 🟢 |
| `bench_db_audit_count_with_entity_filter` | 490 | 460 | 560 | 13 | 🟢 |
| `bench_db_audit_count_with_date_filter` | 500 | 470 | 580 | 14 | 🟢 |

> **Nota:** Los valores son de referencia (ejecución inicial). Para comparar contra baseline usa `--benchmark-compare`. Los tiempos del SELECT FOR UPDATE (`sequence_get_for_update_*`) son altos porque PostgreSQL adquiere y libera un row-level lock en cada iteración sin transacción de commit.

## 📦 Dataset de Prueba

Datos sembrados en la base `PizzaFiori_benchmark` al inicio de cada sesión de pytest.

| Tabla | Registros | Descripción |
|-------|:---------:|-------------|
| `product_categories` | 2 | Pizzas, Empanadas |
| `products` | 10 | 5 por categoría, SKU BENCH-001..010 |
| `product_prices` | 20 | 2 rangos de precio por producto |
| `offers` | 1 | Combo Benchmark (activo) |
| `offer_items` | 2 | 1 ítem por categoría |
| `offer_item_productos` | 2 | Asignación producto a ítem de oferta |
| `expense_categories` | 4 | 2 raíz + 2 subcategorías |
| `expenses` | 30 | Distribuidos en 60 días |
| `sales` | 50 | Distribuidas en 58 días (~28h de separación) |
| `sale_items` | 100 | 2 ítems por venta |
| `users` | 6 | 1 ADMIN + 5 USER |
| `category_stock` | 2 | 1 por categoría de producto |
| `audit_logs` | 40 | 5 entity types × 3 actions × 6 usuarios |
| `order_daily_sequences` | 7 | Últimos 7 días |
| **TOTAL** | **~278** | |

## 🛠️ Stack de Benchmarks

### Dependencias

```txt
pytest==9.0.2                    # Framework base
pytest-benchmark==5.2.3          # Medición estadística con pedantic mode
pytest-asyncio==1.3.0            # Fixtures async (asyncio_mode=auto)
asyncpg==0.30.0                  # Driver PostgreSQL async (via SQLAlchemy)
sqlalchemy==2.0.40               # ORM async (async_sessionmaker)
python-dotenv==1.1.0             # Carga backend/.env.benchmark
matplotlib==3.10.8               # Visualización de resultados (requiere reportes generados)
```

### Herramientas

- **pytest-benchmark:** Mide latencia con estadísticas completas (mean, median, stddev, min, max, IQR). En modo `pedantic` con `rounds=50, iterations=3, warmup_rounds=3`.
- **asyncpg:** Driver nativo async para PostgreSQL. Mucho más rápido que psycopg2 async.
- **async_sessionmaker:** Cada iteración abre y cierra una `AsyncSession` fresca — simula el ciclo de vida real de FastAPI.
- **Base de datos aislada:** `PizzaFiori_benchmark` — completamente separada de producción y desarrollo.

## 📁 Estructura de Benchmarks

```
backend/
├── .env.benchmark                             # Variables de conexión a la BD benchmark
├── benchmark_results/                         # JSONs autogenerados por --benchmark-autosave
│   └── Windows-CPython-3.14-64bit/
│       ├── 0001.json                          # Primera ejecución
│       ├── 0002.json                          # Segunda ejecución (para compare)
│       └── ...
│
└── tests/
    └── benchmarks/
        └── repositories/
            ├── conftest.py                    # Engine, schema lifecycle, seed, fixtures
            ├── bench_db_products.py           # 10 benchmarks — productos y categorías
            ├── bench_db_sales.py              #  8 benchmarks — ventas
            ├── bench_db_expenses.py           # 13 benchmarks — gastos, categorías, ofertas
            ├── bench_db_users.py              #  7 benchmarks — usuarios
            ├── bench_db_stock.py              #  4 benchmarks — stock y secuencias diarias
            └── bench_db_audit.py              #  9 benchmarks — auditoría
```

## 🚀 Comandos Útiles

### Ejecutar Todos los Benchmarks

```bash
# Desde el directorio backend/
cd PizzaFiori/backend

# Ejecutar y guardar resultados automáticamente
.venv/Scripts/pytest tests/benchmarks/repositories --no-cov --benchmark-autosave --benchmark-storage=benchmark_results/

# Con verbose (muestra el nombre de cada benchmark)
.venv/Scripts/pytest tests/benchmarks/repositories --no-cov --benchmark-autosave --benchmark-storage=benchmark_results/ -v
```

### Ejecutar un Módulo Específico

```bash
# Solo ventas
.venv/Scripts/pytest tests/benchmarks/repositories/bench_db_sales.py --no-cov -v

# Solo auditoría
.venv/Scripts/pytest tests/benchmarks/repositories/bench_db_audit.py --no-cov -v

# Un benchmark específico
.venv/Scripts/pytest tests/benchmarks/repositories/bench_db_sales.py::bench_db_sale_list_50 --no-cov -v
```

### Comparar con Baseline

```bash
# Guardar baseline con nombre
.venv/Scripts/pytest tests/benchmarks/repositories --no-cov --benchmark-save=baseline --benchmark-storage=benchmark_results/

# Comparar nueva ejecución con baseline guardado
.venv/Scripts/pytest tests/benchmarks/repositories --no-cov --benchmark-compare=baseline --benchmark-storage=benchmark_results/

# Comparar los dos últimos JSONs autosaveados
.venv/Scripts/pytest tests/benchmarks/repositories --no-cov --benchmark-compare=0001 --benchmark-storage=benchmark_results/
```

### Historial de Ejecuciones

```bash
# Ver todos los resultados guardados
.venv/Scripts/pytest-benchmark compare benchmark_results/Windows-CPython-3.14-64bit/ --sort=mean

# Ver historial en tabla
.venv/Scripts/pytest-benchmark compare benchmark_results/Windows-CPython-3.14-64bit/0001.json benchmark_results/Windows-CPython-3.14-64bit/0002.json
```

### Generar Reporte Visual

```bash
# (Requiere haber ejecutado benchmarks al menos una vez)
python tests/benchmarks/visualize.py

# Abre el PNG generado
start benchmark_results/latest_report.png   # Windows
```

### Opciones Adicionales

```bash
# Ordenar por media
.venv/Scripts/pytest tests/benchmarks/repositories --no-cov --benchmark-sort=mean

# Solo mostrar tabla (sin guardar)
.venv/Scripts/pytest tests/benchmarks/repositories --no-cov --benchmark-disable-gc

# Aumentar rounds para mayor precisión estadística
.venv/Scripts/pytest tests/benchmarks/repositories --no-cov --benchmark-min-rounds=100
```

## 🏗️ Arquitectura de Benchmarks

### Ciclo de Vida de la Sesión

```
pytest session start
    │
    ▼
bench_db_lifecycle (scope=session, autouse=True)
    ├── DROP todas las tablas
    ├── CREATE todas las tablas (refleja modelos actuales)
    ├── _seed() — inserta ~278 registros
    └── _engine.dispose() — libera pool ANTES del yield
         │
         ▼
    [módulos se ejecutan con sus propios event loops]
         │
    ▼
bench_db_lifecycle teardown
    ├── DROP todas las tablas
    └── _engine.dispose()
```

### Patrón Pedantic

Cada benchmark usa el modo `pedantic` para resultados deterministas:

```python
def bench_db_example(benchmark, run_async, session_factory):
    """Descripción de lo que mide este benchmark."""
    async def _call():
        async with session_factory() as session:
            return await SomeRepository(session).some_method()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)
```

| Parámetro | Valor | Significado |
|-----------|:-----:|-------------|
| `rounds` | 50 | Repeticiones con estadísticas independientes |
| `iterations` | 3 | Llamadas por round (media del round = tiempo total / 3) |
| `warmup_rounds` | 3 | Rounds de calentamiento descartados (no afectan estadísticas) |

### Fixtures

| Fixture | Scope | Descripción |
|---------|-------|-------------|
| `bench_db_lifecycle` | `session` | Setup/teardown de la BD completa |
| `seeded_ids` | `session` | Dict con IDs de registros sembrados |
| `event_loop` | `module` | Loop asyncio reutilizado por todos los benchmarks del módulo |
| `run_async` | `module` | Ejecuta coroutines en el `event_loop` del módulo |
| `session_factory` | `module` | `async_sessionmaker` conectado a la BD benchmark |

### ¿Por qué Module-scoped?

Usar `scope="module"` en `event_loop` y `session_factory` garantiza que todos los benchmarks de un mismo archivo compartan el mismo loop asyncio y pool de conexiones. Esto:
- Elimina el overhead de crear/destruir un event loop por benchmark
- Evita el error `Future attached to a different loop` de asyncpg
- Mantiene cada módulo aislado de los demás

## ➕ Agregar un Nuevo Benchmark

### 1. Elegir o Crear el Archivo

Si el repositorio ya tiene un archivo correspondiente (`bench_db_*.py`), agregar la función ahí. Si es un repositorio nuevo, crear un nuevo archivo.

### 2. Escribir la Función

```python
def bench_db_mi_repo_mi_metodo(benchmark, run_async, session_factory):
    """SELECT descripción clara de qué consulta hace y con qué datos."""
    async def _call():
        async with session_factory() as session:
            return await MiRepository(session).mi_metodo(param=valor)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)
```

**Reglas de nomenclatura:**
```
bench_db_{entidad}_{operación}[_{variante}]
```

Ejemplos:
- `bench_db_product_list_all` — listar todos
- `bench_db_sale_count_with_date_filter` — count con filtro
- `bench_db_audit_get_by_date_range_entity_filter` — filtro compuesto

### 3. Si Necesita un ID Sembrado

Agregar el ID en `conftest.py` → `_SEEDED_IDS` y en `_seed()`, luego recibirlo como fixture:

```python
def bench_db_mi_repo_get_by_id(benchmark, run_async, session_factory, seeded_ids):
    mi_id = seeded_ids["mi_entidad_id"]

    async def _call():
        async with session_factory() as session:
            return await MiRepository(session).get_by_id(mi_id)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)
```

### 4. Si Necesita Datos Adicionales

Agregar el seed correspondiente en la función `_seed()` de `conftest.py`. Mantener el mismo estilo: bulk insert por tabla, flush después de cada entidad, guardar IDs en `_SEEDED_IDS`.

### 5. Ejecutar y Verificar

```bash
.venv/Scripts/pytest tests/benchmarks/repositories/bench_db_mi_repo.py --no-cov -v
```

## 🔧 Configuración de Benchmarks

### pytest.ini (backend/)

```ini
[pytest]
# Los benchmarks están excluidos del run normal para no afectar el --cov-fail-under=70
addopts =
    ...
    --ignore=tests/benchmarks

# Marker para identificar benchmarks
markers =
    benchmark: DB-integration benchmarks (require benchmark DB)
```

> Los benchmarks se corren de forma separada e independiente, nunca junto con los tests unitarios.

### .env.benchmark (backend/)

```env
BENCH_DB_USER=postgres
BENCH_DB_PASSWORD=tu_password
BENCH_DB_HOST=localhost
BENCH_DB_PORT=5432
BENCH_DB_NAME=PizzaFiori_benchmark
```

La base de datos debe existir antes de ejecutar los benchmarks:
```sql
-- Crear la BD benchmark (solo una vez)
psql -U postgres -c "CREATE DATABASE PizzaFiori_benchmark;"
```

## 📈 Plan de Mejoras

### Fase 1 (Completado) — Infraestructura Base
- ✅ 6 archivos de benchmark, 51 queries
- ✅ Base de datos aislada con schema propio
- ✅ Modo `pedantic` con `rounds=50, iterations=3`
- ✅ `warmup_rounds=3` para eliminar JIT/cache cold start

### Fase 2 (Siguiente) — Dataset Escalable

Agregar variable de entorno `BENCH_DATASET_SIZE=small|medium|large` para controlar el volumen de datos:

| Tamaño | Productos | Ventas | Gastos | Auditoría |
|--------|:---------:|:------:|:------:|:---------:|
| `small` | 10 | 50 | 30 | 40 |
| `medium` | 100 | 500 | 200 | 400 |
| `large` | 1000 | 5000 | 1000 | 2000 |

```bash
BENCH_DATASET_SIZE=large .venv/Scripts/pytest tests/benchmarks/repositories --no-cov --benchmark-autosave
```

### Fase 3 (Siguiente) — Visualización Automática

El script `tests/benchmarks/visualize.py` genera un reporte visual en `benchmark_results/latest_report.png`:

```bash
python tests/benchmarks/visualize.py
```

Produce:
- Panel 1: Barras horizontales de todos los benchmarks ordenados por media, coloreados por módulo
- Panel 2: Comparación histórica (si existen múltiples JSONs)

### Fase 4 — Regresión en CI

Agregar detección de regresiones en CI con umbral del 20%:

```bash
.venv/Scripts/pytest tests/benchmarks/repositories --no-cov \
  --benchmark-compare=baseline \
  --benchmark-compare-fail=mean:20%
```

## 🔍 Troubleshooting

### `Future attached to a different loop`

**Causa:** asyncpg reutiliza conexiones del pool en un event loop diferente al que las creó.

**Solución:** El conftest llama `await _engine.dispose()` al final de `_seed()` (antes del `yield` del fixture) y también en `event_loop` teardown. Esto asegura que cada módulo empiece con conexiones frescas.

### `pytest.skip: .env.benchmark not found`

**Causa:** No existe el archivo `backend/.env.benchmark`.

**Solución:** Crear el archivo con las variables `BENCH_DB_*` (ver sección de Configuración). La base de datos debe existir previamente.

### `connection refused` / `could not connect to server`

**Causa:** PostgreSQL no está corriendo o la BD benchmark no existe.

**Solución:**
```bash
# Verificar que PostgreSQL está corriendo
pg_ctl status

# Crear la BD si no existe
psql -U postgres -c "CREATE DATABASE PizzaFiori_benchmark;"
```

### Los benchmarks aparecen en el run normal y rompen el coverage

**Causa:** La opción `--ignore=tests/benchmarks` en `pytest.ini` no está activa.

**Solución:** Los benchmarks se corren con `.venv/Scripts/pytest tests/benchmarks/repositories` explícitamente, NO con `python -m pytest` (eso usa `pytest.ini` que los ignora).

### Resultados muy variables (stddev alto)

**Causa:** Procesos en background, GC, o pocas rounds.

**Solución:** Cerrar aplicaciones pesadas, aumentar rounds, o usar `--benchmark-disable-gc` para deshabilitar el GC durante el benchmark.

---

**Última actualización:** Marzo 2026
**Benchmarks totales:** 51
**Tiempo de ejecución:** ~14 segundos

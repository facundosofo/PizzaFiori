# Testing - PizzaFiori

Documentación completa de la suite de tests del proyecto PizzaFiori.

## 📊 Resumen de Tests

**Estado Actual:**
- ✅ **561 tests pasando al 100%**
- ✅ **Coverage: 71.10%** (objetivo: 70%)
- ⚡ Tiempo de ejecución: ~7 segundos

### Distribución de Tests

| Categoría | Cantidad | Archivos |
|-----------|----------|----------|
| **Services (application)** | 279 tests | 17 archivos |
| **Routers (endpoints)** | 168 tests | 11 archivos |
| **Schemas (validación)** | 86 tests | 5 archivos |
| **Infrastructure** | 26 tests | 2 archivos |
| **Parametrizados extras** | 2 tests | — |
| **TOTAL** | **561 tests** | **35 archivos** |

## 🎯 Coverage por Capa

### Application Layer (Services) — 279 tests

| Archivo | Tests | Stmts | Miss | Cover |
|---------|------:|------:|-----:|------:|
| `test_audit_helpers.py` → `audit_helpers.py` | 17 | 70 | 23 | 67% |
| `test_audit_service.py` → `audit_service.py` | 14 | 79 | 7 | 91% |
| `test_dashboard_service.py` → `dashboard_service.py` | 15 | 288 | 94 | 67% |
| `test_expense_analytics_service.py` → `expense_analytics_service.py` | 10 | 315 | 116 | 63% |
| `test_expense_category_service.py` → `expense_category_service.py` | 13 | 110 | 9 | 92% |
| `test_expense_service.py` → `expense_service.py` | 13 | 117 | 9 | 92% |
| `test_jwt_service.py` → `jwt_service.py` | 13 | 30 | 0 | **100%** |
| `test_offer_service.py` → `offer_service.py` | 31 | 184 | 44 | 76% |
| `test_pizza_mitad_mitad_service.py` *(sale_service)* | 10 | — | — | — |
| `test_product_analytics_service.py` → `product_analytics_service.py` | 5 | 134 | 28 | 79% |
| `test_product_category_service.py` → `product_category_service.py` | 14 | 100 | 0 | **100%** |
| `test_product_service.py` → `product_service.py` | 18 | 116 | 19 | 84% |
| `test_sale_service.py` → `sale_service.py` | 45 | 382 | 89 | 77% |
| `test_sale_service_snapshots.py` *(sale_service)* | 9 | — | — | — |
| `test_sales_analytics_service.py` → `sales_analytics_service.py` | 9 | 206 | 30 | 85% |
| `test_stock_service.py` → `stock_service.py` | 18 | 101 | 12 | 88% |
| `test_user_service.py` → `user_service.py` | 25 | 194 | 34 | 82% |

### Presentation Layer — Routers (168 tests)

| Archivo | Tests | Stmts | Miss | Cover |
|---------|------:|------:|-----:|------:|
| `test_audit_router.py` → `audit_router.py` | 5 | 30 | 3 | 90% |
| `test_auth_router.py` → `auth_router.py` | 6 | 34 | 0 | **100%** |
| `test_dashboard_router.py` → `dashboard_router.py` | 39 | 121 | 4 | 97% |
| `test_expense_category_router.py` → `expense_category_router.py` | 11 | 45 | 1 | 98% |
| `test_expense_router.py` → `expense_router.py` | 10 | 62 | 14 | 77% |
| `test_offer_router.py` → `offer_router.py` | 18 | 54 | 2 | 96% |
| `test_product_category_router.py` → `product_category_router.py` | 14 | 54 | 2 | 96% |
| `test_product_router.py` → `product_router.py` | 17 | 70 | 2 | 97% |
| `test_sale_router.py` → `sale_router.py` | 27 | 67 | 14 | 79% |
| `test_stock_router.py` → `stock_router.py` | 9 | 36 | 1 | 97% |
| `test_user_router.py` → `user_router.py` | 12 | 86 | 7 | 92% |

### Presentation Layer — Schemas (86 tests)

| Archivo | Tests | Stmts | Miss | Cover |
|---------|------:|------:|-----:|------:|
| `test_offer_schemas.py` → `offer_schemas.py` | 23 | 79 | 8 | 90% |
| `test_pizza_mitad_mitad_schemas.py` → `sale_schemas.py` | 10 | 72 | 2 | 97% |
| `test_product_category_schemas.py` → `product_category_schemas.py` | 13 | 8 | 0 | **100%** |
| `test_product_schemas.py` → `product_schemas.py` | 20 | 42 | 0 | **100%** |
| `test_sale_schemas.py` → `sale_schemas.py` | 20 | 72 | 2 | 97% |

### Infrastructure Layer (26 tests)

| Archivo | Tests | Stmts | Miss | Cover |
|---------|------:|------:|-----:|------:|
| `test_cache_service.py` → `cache_service.py` | 13 | 20 | 3 | 85% |
| `test_sku_generator.py` → `sku_generator.py` | 13 | 11 | 0 | **100%** |

> **Nota:** El coverage de infrastructure (repositories, unit_of_work, file_service) es menor porque no se conecta a la base de datos real ni al sistema de archivos en los tests unitarios. `report_service.py` (723 stmts, 11% coverage) no tiene tests dedicados ya que genera PDFs que requieren dependencias de rendering.

## 🛠️ Stack de Testing

### Dependencias

```txt
pytest==9.0.2                    # Framework de testing
pytest-asyncio==1.3.0            # Soporte para tests async (asyncio_mode=auto)
pytest-cov==7.0.0                # Coverage reports
httpx==0.28.1                    # Cliente HTTP async para tests
```

### Herramientas de Testing

- **pytest:** Framework principal de testing
- **pytest-asyncio:** Manejo de funciones async/await con `asyncio_mode = auto`
- **pytest-cov:** Medición de cobertura de código con `--cov-fail-under=70`
- **httpx.AsyncClient:** Testing de endpoints HTTP con `ASGITransport`
- **unittest.mock:** `AsyncMock` y `MagicMock` para mocking de servicios y repositorios

## 📁 Estructura de Tests

```
backend/tests/
├── conftest.py                                # Fixtures globales (~650 líneas)
├── helpers.py                                 # Funciones auxiliares (builders de modelos)
├── __init__.py
│
├── application/                               # Tests de lógica de negocio (279 tests)
│   ├── test_audit_helpers.py                 # 17 tests — normalización y snapshot
│   ├── test_audit_service.py                 # 14 tests — registro de auditoría
│   ├── test_dashboard_service.py             # 15 tests — revenue, balance, métricas
│   ├── test_expense_analytics_service.py     # 10 tests — analytics de gastos
│   ├── test_expense_category_service.py      # 13 tests — CRUD categorías de gasto
│   ├── test_expense_service.py               # 13 tests — CRUD gastos
│   ├── test_jwt_service.py                   # 13 tests — JWT tokens
│   ├── test_offer_service.py                 # 31 tests — CRUD ofertas + validación + delete
│   ├── test_pizza_mitad_mitad_service.py     # 10 tests — pizza mitad-mitad
│   ├── test_product_analytics_service.py     #  5 tests — analytics de productos
│   ├── test_product_category_service.py      # 14 tests — CRUD categorías productos
│   ├── test_product_service.py               # 18 tests — CRUD productos + SKU
│   ├── test_sale_service.py                  # 45 tests — CRUD ventas + pricing + pizza helpers
│   ├── test_sale_service_snapshots.py        #  9 tests — snapshots en ventas
│   ├── test_sales_analytics_service.py       #  9 tests — analytics de ventas
│   ├── test_stock_service.py                 # 18 tests — gestión de stock
│   └── test_user_service.py                  # 25 tests — CRUD usuarios + auth
│
├── infrastructure/                            # Tests de infraestructura (26 tests)
│   ├── test_cache_service.py                 # 13 tests — cache en memoria
│   └── test_sku_generator.py                 # 13 tests — generación de SKUs
│
└── presentation/                              # Tests de capa de presentación (254 tests)
    ├── routers/                               # Tests de endpoints HTTP (168 tests)
    │   ├── test_audit_router.py              #  5 tests — endpoints auditoría
    │   ├── test_auth_router.py               #  6 tests — login/register
    │   ├── test_dashboard_router.py          # 39 tests — dashboard completo
    │   ├── test_expense_category_router.py   # 11 tests — endpoints categorías gasto
    │   ├── test_expense_router.py            # 10 tests — endpoints gastos
    │   ├── test_offer_router.py              # 18 tests — endpoints ofertas
    │   ├── test_product_category_router.py   # 14 tests — endpoints categorías producto
    │   ├── test_product_router.py            # 17 tests — endpoints productos
    │   ├── test_sale_router.py               # 27 tests — endpoints ventas
    │   ├── test_stock_router.py              #  9 tests — endpoints stock
    │   └── test_user_router.py               # 12 tests — endpoints usuarios
    │
    └── schemas/                               # Tests de validación Pydantic (86 tests)
        ├── test_offer_schemas.py             # 23 tests — validación ofertas + duplicados
        ├── test_pizza_mitad_mitad_schemas.py  # 10 tests — validación pizza mitad-mitad
        ├── test_product_category_schemas.py  # 13 tests — validación categorías
        ├── test_product_schemas.py           # 20 tests — validación productos
        └── test_sale_schemas.py              # 20 tests — validación ventas + snapshots
```

## 🚀 Comandos Útiles

### Ejecutar Todos los Tests

```bash
# Desde el directorio backend (usa backend/pytest.ini)
cd PizzaFiori/backend
python -m pytest

# Ejecutar con output reducido
python -m pytest -q

# Ejecutar sin coverage (más rápido)
python -m pytest --no-cov
```

### Ejecutar Tests por Categoría

```bash
# Solo tests de services
python -m pytest tests/application/ -v

# Solo tests de routers (endpoints)
python -m pytest tests/presentation/routers/ -v

# Solo tests de schemas
python -m pytest tests/presentation/schemas/ -v

# Solo tests de infrastructure
python -m pytest tests/infrastructure/ -v
```

### Ejecutar Tests Específicos

```bash
# Tests de un módulo específico
python -m pytest tests/application/test_sale_service.py -v

# Un test específico
python -m pytest tests/application/test_sale_service.py::test_delete_sale_success -v

# Tests que coincidan con un patrón
python -m pytest -k "dashboard" -v

# Parar en el primer fallo
python -m pytest -x
```

### Reports de Coverage

```bash
# Coverage con líneas faltantes (incluido por defecto en pytest.ini)
python -m pytest

# Generar reporte HTML (se genera en htmlcov/)
python -m pytest --cov-report=html

# Abrir reporte HTML
start htmlcov/index.html      # Windows
open htmlcov/index.html       # macOS
xdg-open htmlcov/index.html   # Linux

# Coverage sin mínimo requerido
python -m pytest --no-cov
```

### Opciones de Debugging

```bash
# Parar en el primer fallo
python -m pytest -x

# Traceback corto
python -m pytest --tb=short

# Mostrar prints
python -m pytest -s

# Re-ejecutar solo los que fallaron
python -m pytest --lf

# Re-ejecutar fallidos primero, luego el resto
python -m pytest --ff

# Mostrar logs en tiempo real
python -m pytest --log-cli-level=INFO
```

## 🧪 Tipos de Tests

### 1. Tests de Schemas (Pydantic Validation)

**Objetivo:** Validar que los schemas de request/response funcionan correctamente.

**Qué se testea:**
- ✅ Validación de campos requeridos
- ✅ Validación de tipos de datos
- ✅ Validación de constraints (min, max, regex)
- ✅ Valores por defecto
- ✅ Validadores personalizados (duplicados en ofertas, pizza mitad-mitad)
- ✅ Serialización y deserialización

**Ejemplo:**

```python
def test_create_categoria_valid():
    """Schema válido debe pasar la validación"""
    schema = CreateCategoriaRequest(
        nombre="Pizzas",
        descripcion="Pizzas tradicionales"
    )
    assert schema.nombre == "Pizzas"

def test_create_categoria_empty_nombre():
    """Nombre vacío debe fallar la validación"""
    with pytest.raises(ValidationError):
        CreateCategoriaRequest(nombre="")
```

### 2. Tests de Services (Business Logic)

**Objetivo:** Validar la lógica de negocio sin dependencias externas.

**Qué se testea:**
- ✅ Happy paths (flujos exitosos)
- ✅ Edge cases (casos límite)
- ✅ Manejo de errores
- ✅ Validaciones de negocio (pizza mitad-mitad, pricing por rangos)
- ✅ Transacciones y rollbacks
- ✅ Balance y métricas del dashboard
- ✅ Interacción con repositorios (mocked)

**Estrategia de Mocking:**
- Se mockean los repositorios via `mock_uow` (Unit of Work)
- Se usa `AsyncMock` para métodos async
- Se usa `patch.object` para métodos internos del servicio
- Se verifica que se llamen los métodos correctos

**Ejemplo:**

```python
@pytest.mark.asyncio
async def test_delete_sale_success(mock_uow, mock_logger, sample_sale):
    """Eliminar venta exitosamente."""
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.get_by_id.return_value = sample_sale

    result = await service.delete(1)

    assert result.status_code == 204
    mock_uow.sale_repo.delete.assert_called_once_with(1)
    mock_uow.commit.assert_called_once()
```

### 3. Tests de Routers (HTTP Endpoints)

**Objetivo:** Validar que los endpoints HTTP funcionan correctamente.

**Qué se testea:**
- ✅ Status codes correctos (200, 201, 204, 400, 404, 422, 500)
- ✅ Estructura de respuestas JSON
- ✅ Validación de parámetros de request
- ✅ Headers y Content-Type (incluyendo PDF)
- ✅ Query parameters y path parameters
- ✅ Autenticación JWT (bypass con mock)

**Estrategia de Testing:**
- Se usa `httpx.AsyncClient` con `ASGITransport` para llamadas HTTP
- Se mockean los servicios via `dependency-injector` container overrides
- Se usa `@pytest_asyncio.fixture` para el `async_client`
- Se verifica solo la capa HTTP (no la lógica de negocio)

**Ejemplo:**

```python
@pytest.mark.asyncio
async def test_get_balance_metrics(async_client: AsyncClient, mock_dashboard_service):
    """Obtener métricas de balance retorna 200"""
    mock_dashboard_service.get_balance_metrics.return_value.value = {
        "sales": {"current": 250000.0, "previous": 230000.0, "comparison_type": "MoM"},
        "expenses": {"current": 95000.0, "previous": 88000.0, "comparison_type": "MoM"},
        "net_profit": {"sales": 250000.0, "expenses": 95000.0, "net_profit": 155000.0,
                       "previous_net": 142000.0, "comparison_type": "MoM"},
        "net_margin": {"sales": 250000.0, "expenses": 95000.0, "margin": 62.0,
                       "previous_margin": 61.7, "comparison_type": "MoM"},
    }

    response = await async_client.get("/dashboard/balance")

    assert response.status_code == 200
```

## 🔧 Configuración de Tests

### pytest.ini (backend/)

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70
markers =
    unit: Unit tests with mocked dependencies
    integration: Integration tests with real database
    slow: Tests that take longer to run
filterwarnings =
    ignore::DeprecationWarning:pytest_asyncio.plugin
    ignore:.*asyncio\.iscoroutinefunction.*:DeprecationWarning
```

> **Nota:** También existe un `pytest.ini` en la raíz del proyecto para ejecutar desde `PizzaFiori/`. Usa `testpaths = backend/tests` y `--cov=backend/app`.

### Fixtures Principales (conftest.py)

#### Mock UoW y Services

```python
@pytest.fixture
def mock_uow():
    """Mock del Unit of Work con todos los repositorios."""
    uow = AsyncMock()
    uow.product_repo = AsyncMock()
    uow.sale_repo = AsyncMock()
    uow.offer_repo = AsyncMock()
    # ... todos los repos
    return uow

@pytest.fixture
def mock_dashboard_service():
    """Mock del DashboardService para router tests."""
    service = MagicMock()
    result = MagicMock(error=None, status_code=200, value=[])
    service.get_revenue_by_period = AsyncMock(return_value=result)
    service.get_balance_metrics = AsyncMock(return_value=result)
    # ... todos los métodos
    return service
```

#### Async HTTP Client

```python
@pytest_asyncio.fixture
async def async_client(mock_cache_service, mock_product_service, ...):
    """Cliente HTTP async con servicios mockeados."""
    mock_admin_user = {"id": 1, "username": "admin_test", "role": "ADMIN"}

    # Override de servicios con mocks via dependency-injector
    container.product_service.override(mock_product_service)
    # ...

    # Bypass JWT middleware
    application.dependency_overrides[get_current_user] = lambda: mock_admin_user

    try:
        with patch.object(JWTMiddleware, 'dispatch', mock_jwt_dispatch):
            transport = ASGITransport(app=application, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                yield client
    finally:
        container.product_service.reset_override()
        # ...
        application.dependency_overrides.clear()
```

#### Model Builders (helpers.py)

```python
def build_product_model(id, nombre, categoria_id, precios, ...) -> Product:
    """Construir modelo Product para tests."""

def build_sale_model(id, items, ...) -> Sale:
    """Construir modelo Sale para tests."""

def build_category_model(id, nombre, ...) -> Category:
    """Construir modelo Category para tests."""
```

## 📝 Mejores Prácticas

### Estructura AAA (Arrange-Act-Assert)

```python
@pytest.mark.asyncio
async def test_example(mock_uow, mock_logger):
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.get_by_id.return_value = sample_sale

    # Act
    result = await service.get_by_id(1)

    # Assert
    assert result.value.id == 1
    mock_uow.sale_repo.get_by_id.assert_called_once_with(1)
```

### Nomenclatura

```python
# ✅ BIEN: Descriptivo y claro
def test_create_category_duplicate_nombre_raises_error():
async def test_delete_sale_not_found():
def test_es_pizza_by_category():

# ❌ MAL: Poco descriptivo
def test_category():
def test_1():
```

### Tests Independientes

Cada test es independiente gracias a fixtures con scope `function` (por defecto). No se comparte estado entre tests.

### Mocking Específico

Cada test configura su mock de forma explícita para el caso que testea:

```python
# Test de éxito: mock retorna dato
mock_uow.sale_repo.get_by_id.return_value = sample_sale

# Test de no encontrado: mock retorna None
mock_uow.sale_repo.get_by_id.return_value = None

# Test de error: mock lanza excepción
mock_uow.sale_repo.delete.side_effect = Exception("fk constraint")
```

## 📈 CI/CD Integration

### GitHub Actions Ejemplo

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.14'
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    - name: Run tests
      run: |
        cd backend
        python -m pytest --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v4
      with:
        file: ./backend/coverage.xml
```

## 🔄 Mantenimiento de Tests

### Agregar Tests para Nuevos Features

1. **Crear tests de schemas primero** (validación de request/response)
2. **Luego tests de services** (lógica de negocio)
3. **Finalmente tests de routers** (endpoints HTTP)
4. **Actualizar `conftest.py`** si se agregan nuevos servicios (mock + container override)

### Actualizar Tests Cuando Cambie el Código

- Si cambias un modelo → actualiza los helpers (`helpers.py`)
- Si cambias un servicio → verifica que los mocks reflejen el nuevo comportamiento
- Si cambias un endpoint → actualiza el mock data para que coincida con los schemas de respuesta
- Si agregas un servicio nuevo → agregar fixture en `conftest.py` y override en `async_client`

---

**Última actualización:** Marzo 2026
**Coverage actual:** 71.10%
**Tests totales:** 561


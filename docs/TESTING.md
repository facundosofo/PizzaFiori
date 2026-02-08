# Testing - PizzaFiori

Documentación completa de la suite de tests del proyecto PizzaFiori.

## 📊 Resumen de Tests

**Estado Actual:**
- ✅ **254 tests pasando al 100%**
- ✅ **Coverage: 81.18%** (objetivo: 70%)
- ⚡ Tiempo de ejecución: ~1.85 segundos

### Distribución de Tests

| Categoría | Cantidad | Archivos |
|-----------|----------|----------|
| **Schemas** | ~88 tests | 4 archivos |
| **Services** | ~100 tests | 7 archivos |
| **Infrastructure** | 13 tests | 1 archivo |
| **Routers** | ~53 tests | 4 archivos |
| **TOTAL** | **254 tests** | **16 archivos** |

### Nuevos Tests (Snapshot Feature)

| Módulo | Tests | Descripción |
|--------|-------|-------------|
| `test_sale_service_snapshots.py` | 9 tests | Captura de snapshots en ventas + validación ofertas |
| `test_sku_generator.py` | 13 tests | Generación y normalización de SKUs |
| `test_product_service.py` | +3 tests | Auto-generación SKU, validación categoría |
| `test_sale_service.py` | +3 tests | Validación de productos en ofertas con categoría |

## 🎯 Coverage por Capa

### Presentation Layer (Routers y Schemas)
- ✅ **Category Router:** 100%
- ✅ **Product Router:** 100%
- ✅ **Offer Router:** 100%
- ✅ **Sale Router:** 100%
- ✅ **Category Schemas:** 100%
- ✅ **Product Schemas:** 100%
- **Offer Schemas:** 90%
- **Sale Schemas:** 97%

### Application Layer (Services)
- ✅ **CategoryService:** 100%
- ✅ **ProductService:** 100%
- **OfferService:** 83%
- **SaleService:** 63% *(requiere tests adicionales para validación de ofertas)*

### Infrastructure Layer
- ✅ **SKU Generator:** 100%
- **Database:** 83%
- **Logging:** 82%
- **Middleware:** 78%
- **Repositories (base):** 41%
- **Repositories (implementaciones):** 42-89%
- **File Service:** 30%
- **Unit of Work:** 43%

### Domain Layer
- **Models:** 89-94%
- ✅ **Repositories (interfaces):** 100%
- **Unit of Work:** 87%

> **Nota:** El coverage de infrastructure es menor porque no se conecta a la base de datos real ni al sistema de archivos en los tests unitarios. El coverage de SaleService (63%) indica que faltan tests para las nuevas validaciones de ofertas con categorías y productos combinados.

## 🛠️ Stack de Testing

### Dependencias Principales

```txt
pytest==7.4.3                    # Framework de testing
pytest-asyncio==1.3.0            # Soporte para tests async
pytest-cov==4.1.0                # Coverage reports
pytest-mock==3.12.0              # Utilities para mocking
httpx==0.25.2                    # Cliente HTTP async para tests
```

### Herramientas de Testing

- **pytest:** Framework principal de testing
- **pytest-asyncio:** Manejo de funciones async/await
- **pytest-cov:** Medición de cobertura de código
- **pytest-mock:** Creación y gestión de mocks
- **httpx.AsyncClient:** Testing de endpoints HTTP

## 📁 Estructura de Tests

```
backend/tests/
├── conftest.py                           # Fixtures globales (333 líneas)
├── helpers.py                            # Funciones auxiliares (incluye SKU y snapshots)
│
├── presentation/schemas/                 # Tests de validación Pydantic
│   ├── test_category_schemas.py         # 12 tests - validación categorías
│   ├── test_product_schemas.py          # 22 tests - validación productos (incluye SKU)
│   ├── test_offer_schemas.py            # 28 tests - validación ofertas + duplicados
│   └── test_sale_schemas.py             # 26 tests - validación ventas (incluye snapshots)
│
├── application/                          # Tests de lógica de negocio
│   ├── test_category_service.py         # 14 tests - CRUD categorías
│   ├── test_product_service.py          # 19 tests - CRUD productos + SKU + validación
│   ├── test_offer_service.py            # 26 tests - CRUD ofertas + validación duplicados + desactivación
│   ├── test_sale_service.py             # 21 tests - CRUD ventas + pricing con rangos
│   └── test_sale_service_snapshots.py   # 9 tests - snapshot de productos/ofertas + validación (ACTUALIZADO)
│
├── infrastructure/                       # Tests de infraestructura
│   └── test_sku_generator.py            # 13 tests - generación y normalización SKU (NUEVO)
│
└── routers/                              # Tests de endpoints HTTP
    ├── test_category_router.py          # 15 tests - endpoints categorías
    ├── test_product_router.py           # 17 tests - endpoints productos + desactivación
    ├── test_offer_router.py             # 18 tests - endpoints ofertas + desactivación
    └── test_sale_router.py              # 15 tests - endpoints ventas
```

## 🚀 Comandos Útiles

### Ejecutar Todos los Tests

```bash
# Navegar al directorio backend
cd backend

# Ejecutar todos los tests
pytest tests/

# Ejecutar con output verbose
pytest tests/ -v

# Ejecutar con coverage
pytest tests/ --cov=app --cov-report=term-missing
```

### Ejecutar Tests por Categoría

```bash
# Solo tests de schemas
pytest tests/presentation/schemas/ -v

# Solo tests de services
pytest tests/application/ -v

# Solo tests de routers (endpoints)
pytest tests/routers/ -v
```

### Ejecutar Tests Específicos

```bash
# Tests de un módulo específico
pytest tests/routers/test_category_router.py -v

# Un test específico
pytest tests/routers/test_category_router.py::test_create_categoria_exitoso -v

# Tests que coincidan con un patrón
pytest tests/ -k "category" -v
```

### Reports de Coverage

```bash
# Coverage con líneas faltantes
pytest tests/ --cov=app --cov-report=term-missing

# Generar reporte HTML
pytest tests/ --cov=app --cov-report=html

# Abrir reporte HTML (el archivo se genera en htmlcov/index.html)
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html  # Linux

# Coverage mínimo requerido (falla si es menor a 70%)
pytest tests/ --cov=app --cov-fail-under=70
```

### Opciones de Output

```bash
# Traceback corto para errores
pytest tests/ --tb=short

# Traceback de una línea
pytest tests/ --tb=line

# Sin traceback
pytest tests/ --tb=no

# Mostrar print statements
pytest tests/ -s

# Modo verbose + traceback corto
pytest tests/ -v --tb=short
```

### Tests en Watch Mode

```bash
# Ejecutar tests cuando cambien archivos (requiere pytest-watch)
pip install pytest-watch
ptw tests/
```

## 🧪 Tipos de Tests

### 1. Tests de Schemas (Pydantic Validation)

**Objetivo:** Validar que los schemas de request/response funcionan correctamente.

**Qué se testea:**
- ✅ Validación de campos requeridos
- ✅ Validación de tipos de datos
- ✅ Validación de constraints (min, max, regex)
- ✅ Valores por defecto
- ✅ Validadores personalizados
- ✅ Serialización y deserialización

**Ejemplo:**

```python
def test_create_categoria_valid():
    """Schema válido debe pasar la validación"""
    data = {
        "nombre": "Pizzas",
        "descripcion": "Pizzas tradicionales"
    }
    schema = CreateCategoriaRequest(**data)
    assert schema.nombre == "Pizzas"
    assert schema.descripcion == "Pizzas tradicionales"

def test_create_categoria_empty_nombre():
    """Nombre vacío debe fallar la validación"""
    data = {"nombre": ""}
    with pytest.raises(ValidationError):
        CreateCategoriaRequest(**data)
```

### 2. Tests de Services (Business Logic)

**Objetivo:** Validar la lógica de negocio sin dependencias externas.

**Qué se testea:**
- ✅ Happy paths (flujos exitosos)
- ✅ Edge cases (casos límite)
- ✅ Manejo de errores
- ✅ Validaciones de negocio
- ✅ Transacciones y rollbacks
- ✅ Interacción con repositorios (mocked)

**Estrategia de Mocking:**
- Se mockean los repositorios
- Se mockean el Unit of Work
- Se mockean servicios externos (FileService)
- Se verifica que se llamen los métodos correctos

**Ejemplo:**

```python
@pytest.mark.asyncio
async def test_create_category_success(mock_uow, mock_category_repository):
    """Crear categoría exitosamente"""
    # Arrange
    mock_category_repository.get_by_nombre.return_value = None
    mock_category = Category(id=1, nombre="Pizzas", descripcion="Test")
    mock_category_repository.create.return_value = mock_category
    
    service = CategoryService(mock_uow)
    
    # Act
    result = await service.create(
        nombre="Pizzas",
        descripcion="Test"
    )
    
    # Assert
    assert result.value.id == 1
    assert result.value.nombre == "Pizzas"
    mock_category_repository.create.assert_called_once()
    mock_uow.commit.assert_called_once()
```

### 3. Tests de Routers (HTTP Endpoints)

**Objetivo:** Validar que los endpoints HTTP funcionan correctamente.

**Qué se testea:**
- ✅ Status codes correctos (200, 201, 400, 404, 422)
- ✅ Estructura de respuestas JSON
- ✅ Validación de parámetros de request
- ✅ Headers y Content-Type
- ✅ Multipart form data (uploads)
- ✅ Query parameters y path parameters

**Estrategia de Testing:**
- Se usa `httpx.AsyncClient` para llamadas HTTP
- Se mockean los servicios (no se llama a BD)
- Se verifica solo la capa HTTP (no la lógica de negocio)

**Ejemplo:**

```python
@pytest.mark.asyncio
async def test_create_categoria_exitoso(async_client: AsyncClient, mock_category_service):
    """POST /categorias/ con datos válidos retorna 201"""
    # Arrange
    mock_category_service.create.return_value.value = build_category_model(
        id=1, nombre="Pizzas", descripcion="Test"
    )
    
    # Act
    response = await async_client.post(
        "/categorias/",
        json={"nombre": "Pizzas", "descripcion": "Test"}
    )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Pizzas"
    assert data["descripcion"] == "Test"
```

## 🔧 Configuración de Tests

### pytest.ini

```ini
[pytest]
pythonpath = .
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts = 
    -v
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=70
    --tb=short

markers =
    asyncio: marks tests as async
    unit: marks tests as unit tests
    integration: marks tests as integration tests
```

### Fixtures Principales (conftest.py)

#### Mock Services

```python
@pytest.fixture
def mock_category_service():
    """Mock del CategoryService"""
    mock = MagicMock()
    mock.create = AsyncMock()
    mock.get_all = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    
    # Configurar return_value para ServiceResult
    mock.create.return_value = MagicMock(
        error=None,
        status_code=201,
        value=None
    )
    return mock
```

#### Async HTTP Client

```python
@pytest.fixture
async def async_client(
    mock_category_service,
    mock_product_service,
    mock_offer_service,
    mock_sale_service
):
    """Cliente HTTP async con servicios mockeados"""
    from app.main import app as application, container
    
    # Override de servicios con mocks
    container.category_service.override(mock_category_service)
    container.product_service.override(mock_product_service)
    container.offer_service.override(mock_offer_service)
    container.sale_service.override(mock_sale_service)
    
    try:
        async with AsyncClient(app=application, base_url="http://test") as client:
            yield client
    finally:
        # Restaurar servicios originales
        container.category_service.reset_override()
        container.product_service.reset_override()
        container.offer_service.reset_override()
        container.sale_service.reset_override()
```

#### Model Builders (helpers.py)

```python
def build_category_model(
    id: int = 1,
    nombre: str = "Categoría Test",
    descripcion: Optional[str] = None,
    activo: bool = True
) -> Category:
    """Construir modelo Category para tests"""
    return Category(
        id=id,
        nombre=nombre,
        descripcion=descripcion,
        activo=activo
    )
```

## 📝 Mejores Prácticas

### Nomenclatura de Tests

```python
# ✅ BIEN: Descriptivo y claro
def test_create_category_success():
    """Crear categoría exitosamente retorna objeto Category"""
    pass

def test_create_category_duplicate_nombre_raises_error():
    """Crear categoría con nombre duplicado debe lanzar error"""
    pass

# ❌ MAL: Poco descriptivo
def test_category():
    pass

def test_1():
    pass
```

### Estructura AAA (Arrange-Act-Assert)

```python
@pytest.mark.asyncio
async def test_example():
    # Arrange: Preparar datos y mocks
    mock_repo.get_by_id.return_value = build_category_model(id=1)
    service = CategoryService(mock_uow)
    
    # Act: Ejecutar la acción a testear
    result = await service.get_by_id(1)
    
    # Assert: Verificar resultados
    assert result.value.id == 1
    mock_repo.get_by_id.assert_called_once_with(1)
```

### Tests Independientes

```python
# ✅ BIEN: Cada test es independiente
def test_a():
    data = {"nombre": "Test"}
    # ... test logic

def test_b():
    data = {"nombre": "Test"}
    # ... test logic

# ❌ MAL: Tests comparten estado
shared_data = {"nombre": "Test"}

def test_a():
    # Modifica shared_data
    pass

def test_b():
    # Depende del estado de shared_data
    pass
```

### Mocking Específico

```python
# ✅ BIEN: Mock específico para el test
@pytest.mark.asyncio
async def test_get_category_not_found(mock_uow, mock_category_repository):
    mock_category_repository.get_by_id.return_value = None
    
    service = CategoryService(mock_uow)
    result = await service.get_by_id(999)
    
    assert result.error == "Categoría con ID 999 no encontrada"
    assert result.status_code == 404

# ❌ MAL: Mock genérico que no refleja el caso de uso
@pytest.mark.asyncio
async def test_get_category_not_found(mock_category_service):
    # El mock ya tiene configuración por defecto que no aplica
    pass
```

## 🐛 Debugging de Tests

### Ver Output Detallado

```bash
# Mostrar prints
pytest tests/application/test_category_service.py -s

# Verbose + prints
pytest tests/ -sv

# Traceback completo
pytest tests/ --tb=long
```

### Ejecutar Tests Hasta el Primer Fallo

```bash
pytest tests/ -x
```

### Ejecutar Solo Tests Fallidos

```bash
# Primera ejecución (algunos fallan)
pytest tests/

# Re-ejecutar solo los que fallaron
pytest tests/ --lf  # last-failed

# Re-ejecutar fallidos primero, luego el resto
pytest tests/ --ff  # failed-first
```

### Usar el Debugger

```python
def test_example():
    # Agregar breakpoint
    import pdb; pdb.set_trace()
    
    # O usar el nuevo breakpoint() de Python 3.7+
    breakpoint()
    
    result = some_function()
    assert result == expected
```

### Ver Logs en Tests

```bash
# Mostrar logs de nivel INFO y superior
pytest tests/ --log-cli-level=INFO

# Mostrar todos los logs
pytest tests/ --log-cli-level=DEBUG
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
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest tests/ --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./backend/coverage.xml
```

## 🎓 Recursos y Referencias

### Documentación Oficial

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [HTTPX Testing](https://www.python-httpx.org/advanced/#testing)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validators/)

### Tutoriales Relacionados

- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Async Code](https://realpython.com/async-io-python/)
- [Mocking in Python](https://realpython.com/python-mock-library/)

## 🔄 Mantenimiento de Tests

### Agregar Tests para Nuevos Features

1. **Crear tests de schemas primero** (validación)
2. **Luego tests de services** (lógica de negocio)
3. **Finalmente tests de routers** (endpoints HTTP)

### Actualizar Tests Cuando Cambie el Código

- Si cambias un modelo, actualiza los helpers correspondientes
- Si cambias un servicio, verifica que los mocks reflejen el nuevo comportamiento
- Si cambias un endpoint, actualiza tanto el test de router como el de schema

### Refactorizar Tests

- Extrae lógica común a fixtures
- Usa helpers para crear datos de test
- Agrupa tests relacionados en clases
- Documenta casos de uso complejos

---

**Última actualización:** Febrero 2026  
**Coverage actual:** 86%  
**Tests totales:** 234

## 📝 Changelog de Tests

### Febrero 2026 - Snapshot Feature

**Nuevos archivos:**
- `tests/application/test_sale_service_snapshots.py` - 6 tests para captura de snapshots
- `tests/infrastructure/test_sku_generator.py` - 13 tests para generación de SKUs

**Archivos actualizados:**
- `tests/application/test_product_service.py` - +3 tests (SKU auto-generación, validación categoría)
- `tests/presentation/schemas/test_sale_schemas.py` - Actualizado con campos snapshot
- `tests/helpers.py` - Agregado soporte para SKU y snapshots en builders

**Features testeados:**
- ✅ Auto-generación de SKU al crear productos
- ✅ Validación de existencia de categoría antes de crear producto
- ✅ Captura de snapshot de productos en ventas (SKU, nombre, categoría, descripción)
- ✅ Captura de snapshot de ofertas en ventas (productos incluidos, nombres, categorías)
- ✅ Normalización de texto para SKUs (eliminar acentos, caracteres especiales)
- ✅ Manejo de nombres largos en generación de SKUs
- ✅ Preservación de datos históricos en ventas


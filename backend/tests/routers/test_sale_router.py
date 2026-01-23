"""
Tests para los endpoints de ventas
Enfocados en verificar respuestas HTTP correctas, sin verificar mocks
"""
import pytest
from httpx import AsyncClient


# --- Tests de creación ---

@pytest.mark.asyncio
async def test_create_sale_solo_productos(async_client: AsyncClient, mock_sale_service):
    """Crear venta solo con productos retorna 201"""
    from tests.helpers import build_sale_model
    venta = build_sale_model(id=1, total=1200.0)
    mock_sale_service.create.return_value.error = None
    mock_sale_service.create.return_value.value = venta
    
    sale_data = {
        "items": [{"producto_id": 1, "cantidad": 1}]
    }
    
    response = await async_client.post("/ventas/", json=sale_data)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert float(data["total"]) == 1200.0


@pytest.mark.asyncio
async def test_create_sale_solo_ofertas(async_client: AsyncClient, mock_sale_service):
    """Crear venta solo con ofertas retorna 201"""
    from tests.helpers import build_sale_model
    venta = build_sale_model(id=1, total=2000.0)
    mock_sale_service.create.return_value.error = None
    mock_sale_service.create.return_value.value = venta
    
    sale_data = {
        "items": [{"oferta_id": 1, "cantidad": 1}]
    }
    
    response = await async_client.post("/ventas/", json=sale_data)
    
    assert response.status_code == 201
    data = response.json()
    assert float(data["total"]) == 2000.0


@pytest.mark.asyncio
async def test_create_sale_productos_y_ofertas(async_client: AsyncClient, mock_sale_service):
    """Crear venta con productos y ofertas retorna 201"""
    from tests.helpers import build_sale_model
    venta = build_sale_model(id=1, total=3200.0)
    mock_sale_service.create.return_value.error = None
    mock_sale_service.create.return_value.value = venta
    
    sale_data = {
        "items": [
            {"producto_id": 1, "cantidad": 2},
            {"oferta_id": 1, "cantidad": 1}
        ]
    }
    
    response = await async_client.post("/ventas/", json=sale_data)
    
    assert response.status_code == 201
    data = response.json()
    assert float(data["total"]) == 3200.0


@pytest.mark.asyncio
async def test_create_sale_multiples_productos(async_client: AsyncClient, mock_sale_service):
    """Crear venta con múltiples productos retorna 201"""
    from tests.helpers import build_sale_model
    venta = build_sale_model(id=1, total=4500.0)
    mock_sale_service.create.return_value.error = None
    mock_sale_service.create.return_value.value = venta
    
    sale_data = {
        "items": [
            {"producto_id": 1, "cantidad": 2},
            {"producto_id": 2, "cantidad": 1}
        ]
    }
    
    response = await async_client.post("/ventas/", json=sale_data)
    
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_sale_sin_items_retorna_422(async_client: AsyncClient):
    """Crear venta sin productos ni ofertas retorna 422"""
    sale_data = {}
    
    response = await async_client.post("/ventas/", json=sale_data)
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_sale_producto_no_existe_retorna_404(async_client: AsyncClient, mock_sale_service):
    """Crear venta con producto inexistente retorna 404"""
    mock_sale_service.create.return_value.error = "Producto con ID 999 no encontrado"
    mock_sale_service.create.return_value.status_code = 404
    
    sale_data = {
        "items": [{"producto_id": 999, "cantidad": 1}]
    }
    
    response = await async_client.post("/ventas/", json=sale_data)
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_sale_oferta_no_existe_retorna_404(async_client: AsyncClient, mock_sale_service):
    """Crear venta con oferta inexistente retorna 404"""
    mock_sale_service.create.return_value.error = "Oferta con ID 999 no encontrada"
    mock_sale_service.create.return_value.status_code = 404
    
    sale_data = {
        "items": [{"oferta_id": 999, "cantidad": 1}]
    }
    
    response = await async_client.post("/ventas/", json=sale_data)
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_sale_producto_inactivo_retorna_400(async_client: AsyncClient, mock_sale_service):
    """Crear venta con producto inactivo retorna 400"""
    mock_sale_service.create.return_value.error = "El producto está inactivo"
    mock_sale_service.create.return_value.status_code = 400
    
    sale_data = {
        "items": [{"producto_id": 1, "cantidad": 1}]
    }
    
    response = await async_client.post("/ventas/", json=sale_data)
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_sale_oferta_inactiva_retorna_400(async_client: AsyncClient, mock_sale_service):
    """Crear venta con oferta inactiva retorna 400"""
    mock_sale_service.create.return_value.error = "La oferta está inactiva"
    mock_sale_service.create.return_value.status_code = 400
    
    sale_data = {
        "items": [{"oferta_id": 1, "cantidad": 1}]
    }
    
    response = await async_client.post("/ventas/", json=sale_data)
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_sale_cantidad_cero_retorna_422(async_client: AsyncClient):
    """Crear venta con cantidad 0 retorna 422"""
    sale_data = {
        "productos": [{"producto_id": 1, "cantidad": 0}]
    }
    
    response = await async_client.post("/ventas/", json=sale_data)
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_sale_cantidad_negativa_retorna_422(async_client: AsyncClient):
    """Crear venta con cantidad negativa retorna 422"""
    sale_data = {
        "productos": [{"producto_id": 1, "cantidad": -1}]
    }
    
    response = await async_client.post("/ventas/", json=sale_data)
    
    assert response.status_code == 422


# --- Tests de consulta ---

@pytest.mark.asyncio
async def test_get_all_sales_retorna_lista(async_client: AsyncClient, mock_sale_service):
    """Obtener todas las ventas retorna lista 200"""
    from tests.helpers import build_sale_model
    ventas = [
        build_sale_model(id=1, total=1200.0),
        build_sale_model(id=2, total=2500.0),
    ]
    mock_sale_service.get_all.return_value = ventas
    
    response = await async_client.get("/ventas/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_sales_con_paginacion(async_client: AsyncClient, mock_sale_service):
    """Obtener ventas con paginación retorna 200"""
    from tests.helpers import build_sale_model
    ventas = [build_sale_model(id=1, total=1200.0)]
    mock_sale_service.get_all.return_value = ventas
    
    response = await async_client.get("/ventas/?skip=0&limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_sales_skip_negativo_retorna_422(async_client: AsyncClient):
    """Obtener ventas con skip negativo retorna 422"""
    response = await async_client.get("/ventas/?skip=-1")
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_sales_limit_cero_retorna_422(async_client: AsyncClient):
    """Obtener ventas con limit 0 retorna 422"""
    response = await async_client.get("/ventas/?limit=0")
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_sales_limit_excesivo_retorna_422(async_client: AsyncClient):
    """Obtener ventas con limit > 1000 retorna 422"""
    response = await async_client.get("/ventas/?limit=1001")
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_sales_vacia_retorna_lista_vacia(async_client: AsyncClient, mock_sale_service):
    """Obtener ventas cuando no hay ninguna retorna lista vacía"""
    mock_sale_service.get_all.return_value = []
    
    response = await async_client.get("/ventas/")
    
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_sale_por_id_existente(async_client: AsyncClient, mock_sale_service):
    """Obtener venta por ID válido retorna 200"""
    from tests.helpers import build_sale_model
    venta = build_sale_model(id=1, total=1200.0)
    mock_sale_service.get_by_id.return_value.error = None
    mock_sale_service.get_by_id.return_value.value = venta
    
    response = await async_client.get("/ventas/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert float(data["total"]) == 1200.0


@pytest.mark.asyncio
async def test_get_sale_por_id_no_existente_retorna_404(async_client: AsyncClient, mock_sale_service):
    """Obtener venta inexistente retorna 404"""
    mock_sale_service.get_by_id.return_value.error = "Venta no encontrada"
    mock_sale_service.get_by_id.return_value.status_code = 404
    
    response = await async_client.get("/ventas/999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_sale_id_invalido_retorna_422(async_client: AsyncClient):
    """Obtener venta con ID < 1 retorna 422"""
    response = await async_client.get("/ventas/0")
    
    assert response.status_code == 422

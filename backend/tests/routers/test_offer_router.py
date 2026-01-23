"""
Tests para los endpoints de ofertas
Enfocados en verificar respuestas HTTP correctas, sin verificar mocks
"""
import pytest
from httpx import AsyncClient


# --- Tests de creación ---

@pytest.mark.asyncio
async def test_create_offer_exitoso(async_client: AsyncClient, mock_offer_service):
    """Crear oferta con datos válidos retorna 201"""
    from tests.helpers import build_offer_model
    oferta = build_offer_model(id=1, nombre="Promo 2x1", precio=2000.0)
    mock_offer_service.create.return_value.error = None
    mock_offer_service.create.return_value.value = oferta
    
    offer_data = {
        "nombre": "Promo 2x1",
        "precio": 2000.0,
        "productos": [
            {"producto_id": 1, "cantidad": 2}
        ]
    }
    
    response = await async_client.post("/ofertas/", json=offer_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Promo 2x1"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_offer_con_multiples_productos(async_client: AsyncClient, mock_offer_service):
    """Crear oferta con múltiples productos retorna 201"""
    from tests.helpers import build_offer_model
    oferta = build_offer_model(id=1, nombre="Combo Familiar")
    mock_offer_service.create.return_value.error = None
    mock_offer_service.create.return_value.value = oferta
    
    offer_data = {
        "nombre": "Combo Familiar",
        "precio": 5000.0,
        "productos": [
            {"producto_id": 1, "cantidad": 2},
            {"producto_id": 2, "cantidad": 1},
            {"producto_id": 3, "cantidad": 2}
        ]
    }
    
    response = await async_client.post("/ofertas/", json=offer_data)
    
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_offer_producto_no_existe_retorna_404(async_client: AsyncClient, mock_offer_service):
    """Crear oferta con producto inexistente retorna 404"""
    mock_offer_service.create.return_value.error = "Producto con ID 999 no encontrado"
    mock_offer_service.create.return_value.status_code = 404
    
    offer_data = {
        "nombre": "Promo Inválida",
        "precio": 2000.0,
        "productos": [{"producto_id": 999, "cantidad": 1}]
    }
    
    response = await async_client.post("/ofertas/", json=offer_data)
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_offer_productos_duplicados_retorna_422(async_client: AsyncClient):
    """Crear oferta con productos duplicados retorna 422"""
    offer_data = {
        "nombre": "Promo Duplicada",
        "precio_oferta": 2000.0,
        "productos": [
            {"producto_id": 1, "cantidad": 2},
            {"producto_id": 1, "cantidad": 1}
        ]
    }
    
    response = await async_client.post("/ofertas/", json=offer_data)
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_offer_precio_negativo_retorna_422(async_client: AsyncClient):
    """Crear oferta con precio negativo retorna 422"""
    offer_data = {
        "nombre": "Promo",
        "precio_oferta": -100.0,
        "productos": [{"producto_id": 1, "cantidad": 1}]
    }
    
    response = await async_client.post("/ofertas/", json=offer_data)
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_offer_cantidad_cero_retorna_422(async_client: AsyncClient):
    """Crear oferta con cantidad 0 retorna 422"""
    offer_data = {
        "nombre": "Promo",
        "precio_oferta": 2000.0,
        "productos": [{"producto_id": 1, "cantidad": 0}]
    }
    
    response = await async_client.post("/ofertas/", json=offer_data)
    
    assert response.status_code == 422


# --- Tests de consulta ---

@pytest.mark.asyncio
async def test_get_all_offers_retorna_lista(async_client: AsyncClient, mock_offer_service):
    """Obtener todas las ofertas retorna lista 200"""
    from tests.helpers import build_offer_model
    ofertas = [
        build_offer_model(id=1, nombre="Promo 2x1"),
        build_offer_model(id=2, nombre="Combo Familiar"),
    ]
    mock_offer_service.get_all.return_value = ofertas
    
    response = await async_client.get("/ofertas/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_offers_filtrado_por_activo(async_client: AsyncClient, mock_offer_service):
    """Obtener ofertas filtradas por estado activo retorna 200"""
    from tests.helpers import build_offer_model
    ofertas = [build_offer_model(id=1, nombre="Promo 2x1", activo=True)]
    mock_offer_service.get_all.return_value = ofertas
    
    response = await async_client.get("/ofertas/?active=true")
    
    assert response.status_code == 200
    data = response.json()
    assert all(o["activo"] for o in data)


@pytest.mark.asyncio
async def test_get_offers_vacia_retorna_lista_vacia(async_client: AsyncClient, mock_offer_service):
    """Obtener ofertas cuando no hay ninguna retorna lista vacía"""
    mock_offer_service.get_all.return_value = []
    
    response = await async_client.get("/ofertas/")
    
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_offer_por_id_existente(async_client: AsyncClient, mock_offer_service):
    """Obtener oferta por ID válido retorna 200"""
    from tests.helpers import build_offer_model
    oferta = build_offer_model(id=1, nombre="Promo 2x1")
    mock_offer_service.get_by_id.return_value.error = None
    mock_offer_service.get_by_id.return_value.value = oferta
    
    response = await async_client.get("/ofertas/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["nombre"] == "Promo 2x1"


@pytest.mark.asyncio
async def test_get_offer_por_id_no_existente_retorna_404(async_client: AsyncClient, mock_offer_service):
    """Obtener oferta inexistente retorna 404"""
    mock_offer_service.get_by_id.return_value.error = "Oferta no encontrada"
    mock_offer_service.get_by_id.return_value.status_code = 404
    
    response = await async_client.get("/ofertas/999")
    
    assert response.status_code == 404


# --- Tests de actualización ---

@pytest.mark.asyncio
async def test_update_offer_nombre_exitoso(async_client: AsyncClient, mock_offer_service):
    """Actualizar nombre de oferta retorna 200"""
    from tests.helpers import build_offer_model
    oferta = build_offer_model(id=1, nombre="Promo 2x1 Especial")
    mock_offer_service.update.return_value.error = None
    mock_offer_service.update.return_value.value = oferta
    
    update_data = {"nombre": "Promo 2x1 Especial"}
    
    response = await async_client.put("/ofertas/1", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == "Promo 2x1 Especial"


@pytest.mark.asyncio
async def test_update_offer_precio_exitoso(async_client: AsyncClient, mock_offer_service):
    """Actualizar precio de oferta retorna 200"""
    from tests.helpers import build_offer_model
    oferta = build_offer_model(id=1, nombre="Promo 2x1", precio=2500.0)
    mock_offer_service.update.return_value.error = None
    mock_offer_service.update.return_value.value = oferta
    
    update_data = {"precio": 2500.0}
    
    response = await async_client.put("/ofertas/1", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert float(data["precio"]) == 2500.0


@pytest.mark.asyncio
async def test_update_offer_productos_exitoso(async_client: AsyncClient, mock_offer_service):
    """Actualizar productos de oferta retorna 200"""
    from tests.helpers import build_offer_model
    oferta = build_offer_model(id=1, nombre="Promo 2x1")
    mock_offer_service.update.return_value.error = None
    mock_offer_service.update.return_value.value = oferta
    
    update_data = {
        "productos": [
            {"producto_id": 2, "cantidad": 3}
        ]
    }
    
    response = await async_client.put("/ofertas/1", json=update_data)
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_offer_no_existente_retorna_404(async_client: AsyncClient, mock_offer_service):
    """Actualizar oferta inexistente retorna 404"""
    mock_offer_service.update.return_value.error = "Oferta no encontrada"
    mock_offer_service.update.return_value.status_code = 404
    
    update_data = {"nombre": "Nueva Promo"}
    
    response = await async_client.put("/ofertas/999", json=update_data)
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_offer_producto_no_existe_retorna_404(async_client: AsyncClient, mock_offer_service):
    """Actualizar oferta con producto inexistente retorna 404"""
    mock_offer_service.update.return_value.error = "Producto con ID 999 no encontrado"
    mock_offer_service.update.return_value.status_code = 404
    
    update_data = {
        "productos": [{"producto_id": 999, "cantidad": 1}]
    }
    
    response = await async_client.put("/ofertas/1", json=update_data)
    
    assert response.status_code == 404


# --- Tests de desactivación ---

@pytest.mark.asyncio
async def test_deactivate_offer_exitoso(async_client: AsyncClient, mock_offer_service):
    """Desactivar oferta existente retorna 200"""
    from tests.helpers import build_offer_model
    oferta = build_offer_model(id=1, nombre="Promo 2x1", activo=False)
    mock_offer_service.update.return_value.error = None
    mock_offer_service.update.return_value.value = oferta
    
    response = await async_client.patch("/ofertas/1/desactivar")
    
    assert response.status_code == 200
    data = response.json()
    assert data["activo"] is False


@pytest.mark.asyncio
async def test_deactivate_offer_no_existente_retorna_404(async_client: AsyncClient, mock_offer_service):
    """Desactivar oferta inexistente retorna 404"""
    mock_offer_service.update.return_value.error = "Oferta no encontrada"
    mock_offer_service.update.return_value.status_code = 404
    
    response = await async_client.patch("/ofertas/999/desactivar")
    
    assert response.status_code == 404

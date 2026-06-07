"""
Tests para los endpoints de productos
Enfocados en verificar respuestas HTTP correctas, sin verificar mocks
"""
import pytest
from httpx import AsyncClient
from io import BytesIO


# --- Tests de creación ---

@pytest.mark.asyncio
async def test_create_producto_exitoso(async_client: AsyncClient, mock_product_service):
    """Crear producto con datos válidos retorna 201"""
    from tests.helpers import build_product_model
    producto = build_product_model(id=1, nombre="Pizza Muzza", categoria_id=1)
    mock_product_service.create.return_value.error = None
    mock_product_service.create.return_value.value = producto
    
    form_data = {
        "nombre": "Pizza Muzza",
        "categoria_id": 1,
        "precios": '[{"cantidad": 1, "precio": 1200}]'
    }
    
    response = await async_client.post("/productos/", data=form_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Pizza Muzza"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_producto_con_imagen(async_client: AsyncClient, mock_product_service):
    """Crear producto con imagen retorna 201"""
    from tests.helpers import build_product_model
    producto = build_product_model(id=1, nombre="Empanada de Carne", imagen="uploads/productos/test.jpg")
    mock_product_service.create.return_value.error = None
    mock_product_service.create.return_value.value = producto
    
    form_data = {
        "nombre": "Pizza Muzza",
        "categoria_id": 1,
        "precios": '[{"cantidad": 1, "precio": 1200}]'
    }
    files = {"imagen": ("test.jpg", BytesIO(b"fake image"), "image/jpeg")}
    
    response = await async_client.post("/productos/", data=form_data, files=files)
    
    assert response.status_code == 201
    data = response.json()
    assert data["imagen"] == "uploads/productos/test.jpg"


@pytest.mark.asyncio
async def test_create_producto_precios_invalidos_retorna_400(async_client: AsyncClient):
    """Crear producto con JSON de precios inválido retorna 400"""
    form_data = {
        "nombre": "Pizza Muzza",
        "categoria_id": 1,
        "precios": "esto no es json"
    }
    
    response = await async_client.post("/productos/", data=form_data)
    
    assert response.status_code == 400
    assert "JSON válido" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_producto_categoria_no_existe_retorna_404(async_client: AsyncClient, mock_product_service):
    """Crear producto con categoría inexistente retorna 404"""
    mock_product_service.create.return_value.error = "Categoría no encontrada"
    mock_product_service.create.return_value.status_code = 404
    
    form_data = {
        "nombre": "Pizza Muzza",
        "categoria_id": 999,
        "precios": '[{"cantidad": 1, "precio": 1200}]'
    }
    
    response = await async_client.post("/productos/", data=form_data)
    
    assert response.status_code == 404


# --- Tests de consulta ---

@pytest.mark.asyncio
async def test_get_all_productos_retorna_lista(async_client: AsyncClient, mock_product_service):
    """Obtener todos los productos retorna lista 200"""
    from tests.helpers import build_product_model
    productos = [
        build_product_model(id=1, nombre="Pizza Muzza"),
        build_product_model(id=2, nombre="Pizza Napolitana"),
    ]
    mock_product_service.get_all.return_value = productos
    
    response = await async_client.get("/productos/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_productos_filtrado_por_categoria(async_client: AsyncClient, mock_product_service):
    """Obtener productos filtrados por categoría retorna 200"""
    from tests.helpers import build_product_model
    productos = [build_product_model(id=1, nombre="Pizza Muzza", categoria_id=1)]
    mock_product_service.get_all.return_value = productos
    
    response = await async_client.get("/productos/?categoria=1")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["categoria_id"] == 1


@pytest.mark.asyncio
async def test_get_productos_filtrado_por_activo(async_client: AsyncClient, mock_product_service):
    """Obtener productos filtrados por estado activo retorna 200"""
    from tests.helpers import build_product_model
    productos = [build_product_model(id=1, nombre="Pizza Muzza", activo=True)]
    mock_product_service.get_all.return_value = productos
    
    response = await async_client.get("/productos/?active=true")
    
    assert response.status_code == 200
    data = response.json()
    assert all(p["activo"] for p in data)


@pytest.mark.asyncio
async def test_get_producto_por_id_existente(async_client: AsyncClient, mock_product_service):
    """Obtener producto por ID válido retorna 200"""
    from tests.helpers import build_product_model
    producto = build_product_model(id=1, nombre="Pizza Muzza")
    mock_product_service.get_by_id.return_value.error = None
    mock_product_service.get_by_id.return_value.value = producto
    
    response = await async_client.get("/productos/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["nombre"] == "Pizza Muzza"


@pytest.mark.asyncio
async def test_get_producto_por_id_no_existente_retorna_404(async_client: AsyncClient, mock_product_service):
    """Obtener producto inexistente retorna 404"""
    mock_product_service.get_by_id.return_value.error = "Producto no encontrado"
    mock_product_service.get_by_id.return_value.status_code = 404
    
    response = await async_client.get("/productos/999")
    
    assert response.status_code == 404


# --- Tests de actualización ---

@pytest.mark.asyncio
async def test_update_producto_nombre_exitoso(async_client: AsyncClient, mock_product_service):
    """Actualizar solo nombre del producto retorna 200"""
    from tests.helpers import build_product_model
    producto = build_product_model(id=1, nombre="Pizza Muzza Especial")
    mock_product_service.update.return_value.error = None
    mock_product_service.update.return_value.value = producto
    
    form_data = {"nombre": "Pizza Muzza Especial"}
    
    response = await async_client.put("/productos/1", data=form_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == "Pizza Muzza Especial"


@pytest.mark.asyncio
async def test_update_producto_precios_exitoso(async_client: AsyncClient, mock_product_service):
    """Actualizar precios del producto retorna 200"""
    from tests.helpers import build_product_model
    producto = build_product_model(id=1, nombre="Pizza Muzza")
    mock_product_service.update.return_value.error = None
    mock_product_service.update.return_value.value = producto
    
    form_data = {
        "precios": '[{"cantidad": 1, "precio": 1500}, {"cantidad": 2, "precio": 2800}]'
    }
    
    response = await async_client.put("/productos/1", data=form_data)
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_producto_con_imagen(async_client: AsyncClient, mock_product_service):
    """Actualizar producto con nueva imagen retorna 200"""
    from tests.helpers import build_product_model
    producto = build_product_model(id=1, nombre="Empanada de Carne", imagen="uploads/productos/nueva.jpg")
    mock_product_service.update.return_value.error = None
    mock_product_service.update.return_value.value = producto
    
    form_data = {"nombre": "Pizza Muzza"}
    files = {"imagen": ("nueva.jpg", BytesIO(b"new image"), "image/jpeg")}
    
    response = await async_client.put("/productos/1", data=form_data, files=files)
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_producto_no_existente_retorna_404(async_client: AsyncClient, mock_product_service):
    """Actualizar producto inexistente retorna 404"""
    mock_product_service.update.return_value.error = "Producto no encontrado"
    mock_product_service.update.return_value.status_code = 404
    
    form_data = {"nombre": "Pizza Nueva"}
    
    response = await async_client.put("/productos/999", data=form_data)
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_producto_precios_invalidos_retorna_400(async_client: AsyncClient):
    """Actualizar producto con JSON de precios inválido retorna 400"""
    form_data = {"precios": "json invalido"}
    
    response = await async_client.put("/productos/1", data=form_data)
    
    assert response.status_code == 400
    assert "JSON válido" in response.json()["detail"]


# --- Tests de desactivación ---

@pytest.mark.asyncio
async def test_deactivate_producto_exitoso(async_client: AsyncClient, mock_product_service, mock_offer_service):
    """Desactivar producto existente retorna 200 con ofertas desactivadas"""
    from tests.helpers import build_product_model
    from unittest.mock import AsyncMock
    
    producto = build_product_model(id=1, nombre="Pizza Muzza", activo=False)
    mock_product_service.update.return_value.error = None
    mock_product_service.update.return_value.value = producto
    mock_offer_service.deactivate_by_product = AsyncMock(return_value=[5, 10])
    
    response = await async_client.patch("/productos/1/desactivar")
    
    assert response.status_code == 200
    data = response.json()
    assert data["ofertas_desactivadas"] == [5, 10]
    assert data["activo"] == False
    
    # Verificar que se llamaron los métodos correctos
    mock_product_service.update.assert_called_once_with(1, active=False, username='admin_test', is_logical_delete=True)
    mock_offer_service.deactivate_by_product.assert_called_once_with(1, username='admin_test')
    data = response.json()
    assert data["activo"] is False
    assert data["ofertas_desactivadas"] == [5, 10]


@pytest.mark.asyncio
async def test_deactivate_producto_sin_ofertas(async_client: AsyncClient, mock_product_service, mock_offer_service):
    """Desactivar producto sin ofertas retorna 200 con ofertas_desactivadas None"""
    from tests.helpers import build_product_model
    from unittest.mock import AsyncMock
    
    producto = build_product_model(id=1, nombre="Pizza Muzza", activo=False)
    mock_product_service.update.return_value.error = None
    mock_product_service.update.return_value.value = producto
    mock_offer_service.deactivate_by_product = AsyncMock(return_value=[])
    
    response = await async_client.patch("/productos/1/desactivar")
    
    assert response.status_code == 200
    data = response.json()
    assert data["activo"] is False
    assert data["ofertas_desactivadas"] is None


@pytest.mark.asyncio
async def test_deactivate_producto_no_existente_retorna_404(async_client: AsyncClient, mock_product_service, mock_offer_service):
    """Desactivar producto inexistente retorna 404"""
    from unittest.mock import AsyncMock
    
    mock_product_service.update.return_value.error = "Producto no encontrado"
    mock_product_service.update.return_value.status_code = 404
    mock_offer_service.deactivate_by_product = AsyncMock(return_value=[])
    
    response = await async_client.patch("/productos/999/desactivar")
    
    assert response.status_code == 404
    # Verificar que NO se llamó al servicio de ofertas cuando falla el producto
    mock_offer_service.deactivate_by_product.assert_not_called()


# --- Tests de actualización masiva de precios ---

@pytest.mark.asyncio
async def test_bulk_update_prices_con_monto_exitoso(async_client: AsyncClient, mock_product_service):
    """Actualizar precios masivamente con monto fijo retorna 200"""
    from tests.helpers import build_product_model

    productos = [
        build_product_model(id=1, nombre="Empanada de Carne"),
        build_product_model(id=2, nombre="Empanada de Pollo"),
    ]
    mock_product_service.bulk_update_prices.return_value.error = None
    mock_product_service.bulk_update_prices.return_value.value = {
        "productos_actualizados": 2,
        "productos": productos,
    }

    response = await async_client.patch(
        "/productos/actualizar-precios",
        json={"monto": 200},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["productos_actualizados"] == 2
    assert len(data["productos"]) == 2


@pytest.mark.asyncio
async def test_bulk_update_prices_con_porcentaje_exitoso(async_client: AsyncClient, mock_product_service):
    """Actualizar precios masivamente con porcentaje retorna 200"""
    from tests.helpers import build_product_model

    productos = [build_product_model(id=1, nombre="Pizza Muzza")]
    mock_product_service.bulk_update_prices.return_value.error = None
    mock_product_service.bulk_update_prices.return_value.value = {
        "productos_actualizados": 1,
        "productos": productos,
    }

    response = await async_client.patch(
        "/productos/actualizar-precios",
        json={"porcentaje": 10, "categoria_ids": [1]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["productos_actualizados"] == 1


@pytest.mark.asyncio
async def test_bulk_update_prices_sin_monto_ni_porcentaje_retorna_422(async_client: AsyncClient):
    """Actualizar precios sin monto ni porcentaje retorna 422"""
    response = await async_client.patch(
        "/productos/actualizar-precios",
        json={},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_bulk_update_prices_con_ambos_retorna_422(async_client: AsyncClient):
    """Actualizar precios con monto y porcentaje a la vez retorna 422"""
    response = await async_client.patch(
        "/productos/actualizar-precios",
        json={"monto": 200, "porcentaje": 10},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_bulk_update_prices_sin_productos_retorna_404(async_client: AsyncClient, mock_product_service):
    """Actualizar precios sin productos encontrados retorna 404"""
    mock_product_service.bulk_update_prices.return_value.error = "No se encontraron productos activos para actualizar"
    mock_product_service.bulk_update_prices.return_value.status_code = 404

    response = await async_client.patch(
        "/productos/actualizar-precios",
        json={"monto": 200, "categoria_ids": [999]},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_bulk_update_prices_precio_negativo_retorna_400(async_client: AsyncClient, mock_product_service):
    """Actualizar precios que resultan en valor negativo retorna 400"""
    mock_product_service.bulk_update_prices.return_value.error = "El precio del producto 'Empanada' resultaría en $-100"
    mock_product_service.bulk_update_prices.return_value.status_code = 400

    response = await async_client.patch(
        "/productos/actualizar-precios",
        json={"monto": -99999},
    )

    assert response.status_code == 400
"""
Tests para los endpoints de categorías
Enfocados en verificar respuestas HTTP correctas, sin verificar mocks
"""
import pytest
from httpx import AsyncClient


# --- Tests de creación ---

@pytest.mark.asyncio
async def test_create_categoria_exitoso(async_client: AsyncClient, mock_category_service):
    """Crear categoría con datos válidos devuelve 201"""
    categoria_data = {"nombre": "Bebidas"}
    
    from tests.helpers import build_category_model
    categoria_creada = build_category_model(id=1, nombre="Bebidas")
    mock_category_service.create.return_value.error = None
    mock_category_service.create.return_value.value = categoria_creada
    
    response = await async_client.post("/categorias/", json=categoria_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Bebidas"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_categoria_nombre_vacio_retorna_422(async_client: AsyncClient):
    """Crear categoría con nombre vacío retorna 422 Validation Error"""
    categoria_data = {"nombre": ""}
    
    response = await async_client.post("/categorias/", json=categoria_data)
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_categoria_nombre_muy_largo_retorna_422(async_client: AsyncClient):
    """Crear categoría con nombre > 50 caracteres retorna 422"""
    categoria_data = {"nombre": "A" * 51}
    
    response = await async_client.post("/categorias/", json=categoria_data)
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_categoria_duplicada_retorna_400(async_client: AsyncClient, mock_category_service):
    """Crear categoría duplicada retorna 400"""
    categoria_data = {"nombre": "Bebidas"}
    
    mock_category_service.create.return_value.error = "Ya existe una categoría con ese nombre"
    mock_category_service.create.return_value.status_code = 400
    
    response = await async_client.post("/categorias/", json=categoria_data)
    
    assert response.status_code == 400
    assert "Ya existe" in response.json()["detail"]


# --- Tests de consulta ---

@pytest.mark.asyncio
async def test_get_all_categorias_retorna_lista(async_client: AsyncClient, mock_category_service):
    """Obtener todas las categorías retorna lista 200"""
    from tests.helpers import build_category_model
    categorias = [
        build_category_model(id=1, nombre="Bebidas"),
        build_category_model(id=2, nombre="Pizzas"),
    ]
    mock_category_service.get_all.return_value = categorias
    
    response = await async_client.get("/categorias/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["nombre"] == "Bebidas"


@pytest.mark.asyncio
async def test_get_all_categorias_vacia_retorna_lista_vacia(async_client: AsyncClient, mock_category_service):
    """Obtener categorías cuando no hay ninguna retorna lista vacía"""
    mock_category_service.get_all.return_value = []
    
    response = await async_client.get("/categorias/")
    
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_categoria_por_id_existente(async_client: AsyncClient, mock_category_service):
    """Obtener categoría por ID válido retorna 200"""
    from tests.helpers import build_category_model
    categoria = build_category_model(id=1, nombre="Bebidas")
    mock_category_service.get_by_id.return_value.error = None
    mock_category_service.get_by_id.return_value.value = categoria
    
    response = await async_client.get("/categorias/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["nombre"] == "Bebidas"


@pytest.mark.asyncio
async def test_get_categoria_por_id_no_existente_retorna_404(async_client: AsyncClient, mock_category_service):
    """Obtener categoría inexistente retorna 404"""
    mock_category_service.get_by_id.return_value.error = "Categoría no encontrada"
    mock_category_service.get_by_id.return_value.status_code = 404
    
    response = await async_client.get("/categorias/999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_categoria_id_invalido_retorna_422(async_client: AsyncClient):
    """Obtener categoría con ID < 1 retorna 422"""
    response = await async_client.get("/categorias/0")
    
    assert response.status_code == 422


# --- Tests de actualización ---

@pytest.mark.asyncio
async def test_update_categoria_exitoso(async_client: AsyncClient, mock_category_service):
    """Actualizar categoría con datos válidos retorna 200"""
    from tests.helpers import build_category_model
    categoria_actualizada = build_category_model(id=1, nombre="Bebidas Frías")
    mock_category_service.update.return_value.error = None
    mock_category_service.update.return_value.value = categoria_actualizada
    
    response = await async_client.put("/categorias/1", json={"nombre": "Bebidas Frías"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == "Bebidas Frías"


@pytest.mark.asyncio
async def test_update_categoria_no_existente_retorna_404(async_client: AsyncClient, mock_category_service):
    """Actualizar categoría inexistente retorna 404"""
    mock_category_service.update.return_value.error = "Categoría no encontrada"
    mock_category_service.update.return_value.status_code = 404
    
    response = await async_client.put("/categorias/999", json={"nombre": "Nueva"})
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_categoria_nombre_duplicado_retorna_400(async_client: AsyncClient, mock_category_service):
    """Actualizar categoría a nombre duplicado retorna 400"""
    mock_category_service.update.return_value.error = "Ya existe una categoría con ese nombre"
    mock_category_service.update.return_value.status_code = 400
    
    response = await async_client.put("/categorias/1", json={"nombre": "Pizzas"})
    
    assert response.status_code == 400


# --- Tests de eliminación ---

@pytest.mark.asyncio
async def test_delete_categoria_exitoso(async_client: AsyncClient, mock_category_service):
    """Eliminar categoría existente retorna 200"""
    mock_category_service.delete.return_value.error = None
    
    response = await async_client.delete("/categorias/1")
    
    assert response.status_code == 200
    data = response.json()
    assert "detalle" in data
    assert "eliminada" in data["detalle"].lower()


@pytest.mark.asyncio
async def test_delete_categoria_no_existente_retorna_404(async_client: AsyncClient, mock_category_service):
    """Eliminar categoría inexistente retorna 404"""
    mock_category_service.delete.return_value.error = "Categoría no encontrada"
    mock_category_service.delete.return_value.status_code = 404
    
    response = await async_client.delete("/categorias/999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_categoria_con_productos_retorna_400(async_client: AsyncClient, mock_category_service):
    """Eliminar categoría con productos asociados retorna 400"""
    mock_category_service.delete.return_value.error = "No se puede eliminar una categoría con productos asociados"
    mock_category_service.delete.return_value.status_code = 400
    
    response = await async_client.delete("/categorias/1")
    
    assert response.status_code == 400
    assert "productos asociados" in response.json()["detail"].lower()

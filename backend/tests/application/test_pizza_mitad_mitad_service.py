"""Tests para el servicio de pizzas mitad-mitad."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.application.sale_service import SaleService, ServiceResult
from app.domain.models.product import Product
from app.domain.models.product_category import ProductCategory as Category
from app.presentation.schemas.sale_schemas import PizzaMitadMitadRequest


class TestPizzaMitadMitadService:
    """Tests para la funcionalidad de pizzas mitad-mitad en SaleService."""

    @pytest.fixture
    def mock_uow(self):
        """Mock unit of work."""
        uow = AsyncMock()
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        return uow

    @pytest.fixture
    def sale_service(self, mock_uow):
        """Sale service instance."""
        return SaleService(uow=mock_uow, logger=None)

    @pytest.fixture
    def pizza_category(self):
        """Pizza category fixture."""
        category = Category()
        category.id = 1
        category.nombre = "Pizzas"
        return category

    @pytest.fixture
    def muzzarella_product(self, pizza_category):
        """Muzzarella pizza fixture."""
        product = Product()
        product.id = 1
        product.nombre = "Pizza Muzzarella"
        product.categoria = pizza_category
        product.categoria_id = pizza_category.id
        product.activo = True
        # Mock prices
        product.precios = [
            MagicMock(cantidad=1, precio=Decimal("8000"))
        ]
        return product

    @pytest.fixture
    def carne_product(self, pizza_category):
        """Carne pizza fixture."""
        product = Product()
        product.id = 2
        product.nombre = "Pizza Carne"
        product.categoria = pizza_category
        product.categoria_id = pizza_category.id
        product.activo = True
        # Mock prices
        product.precios = [
            MagicMock(cantidad=1, precio=Decimal("10000"))
        ]
        return product

    @pytest.fixture
    def pizza_mitad_mitad_request(self):
        """Pizza mitad-mitad request fixture."""
        return PizzaMitadMitadRequest(
            producto_id_izquierda=1,
            producto_id_derecha=2,
            cantidad=2
        )

    def test_get_pizza_mitad_mitad_price(self, sale_service, muzzarella_product, carne_product):
        """Test pizza mitad-mitad price calculation."""
        price = sale_service._get_pizza_mitad_mitad_price(muzzarella_product, carne_product)
        
        # Should return the price of the more expensive pizza (Carne: 10000)
        assert price == Decimal("10000")

    def test_get_pizza_mitad_mitad_price_reverse(self, sale_service, muzzarella_product, carne_product):
        """Test pizza mitad-mitad price calculation (reverse order)."""
        price = sale_service._get_pizza_mitad_mitad_price(carne_product, muzzarella_product)
        
        # Should still return the price of the more expensive pizza (Carne: 10000)
        assert price == Decimal("10000")

    def test_es_pizza_by_category(self, sale_service, muzzarella_product):
        """Test pizza detection by category."""
        assert sale_service._es_pizza(muzzarella_product) is True

    def test_es_pizza_by_name(self, sale_service):
        """Test pizza detection by name."""
        product = Product()
        product.nombre = "Pizza Napolitana"
        product.categoria = None
        product.activo = True
        
        assert sale_service._es_pizza(product) is True

    def test_es_pizza_not_pizza(self, sale_service):
        """Test that non-pizza products return False."""
        product = Product()
        product.nombre = "Empanada de Carne"
        product.categoria = None
        product.activo = True
        
        assert sale_service._es_pizza(product) is False

    @pytest.mark.asyncio
    async def test_validate_pizza_mitad_mitad_success(self, sale_service, mock_uow, muzzarella_product, carne_product, pizza_mitad_mitad_request):
        """Test successful pizza mitad-mitad validation."""
        # Mock product repository
        mock_uow.product_repo.get_by_id.side_effect = [muzzarella_product, carne_product]
        
        result = await sale_service._validate_pizza_mitad_mitad(pizza_mitad_mitad_request, mock_uow)
        
        assert result is None  # No error means validation passed

    @pytest.mark.asyncio
    async def test_validate_pizza_mitad_mitad_product_not_found(self, sale_service, mock_uow, pizza_mitad_mitad_request):
        """Test validation when product is not found."""
        # Mock product repository to return None for first product
        mock_uow.product_repo.get_by_id.side_effect = [None, MagicMock()]
        
        result = await sale_service._validate_pizza_mitad_mitad(pizza_mitad_mitad_request, mock_uow)
        
        assert result is not None
        assert result.status_code == 404
        assert "no encontrado" in result.error

    @pytest.mark.asyncio
    async def test_validate_pizza_mitad_mitad_inactive_product(self, sale_service, mock_uow, muzzarella_product, carne_product, pizza_mitad_mitad_request):
        """Test validation when product is inactive."""
        # Make one product inactive
        muzzarella_product.activo = False
        
        # Mock product repository
        mock_uow.product_repo.get_by_id.side_effect = [muzzarella_product, carne_product]
        
        result = await sale_service._validate_pizza_mitad_mitad(pizza_mitad_mitad_request, mock_uow)
        
        assert result is not None
        assert result.status_code == 400
        assert "activos" in result.error

    @pytest.mark.asyncio
    async def test_validate_pizza_mitad_mitad_not_pizza(self, sale_service, mock_uow, pizza_mitad_mitad_request):
        """Test validation when product is not a pizza."""
        # Create non-pizza products
        empanada = Product()
        empanada.id = 1
        empanada.nombre = "Empanada Carne"
        empanada.categoria = None
        empanada.activo = True
        
        factura = Product()
        factura.id = 2
        factura.nombre = "Factura"
        factura.categoria = None
        factura.activo = True
        
        # Mock product repository
        mock_uow.product_repo.get_by_id.side_effect = [empanada, factura]
        
        result = await sale_service._validate_pizza_mitad_mitad(pizza_mitad_mitad_request, mock_uow)
        
        assert result is not None
        assert result.status_code == 400
        assert "pizzas" in result.error

    @pytest.mark.asyncio
    async def test_validate_pizza_mitad_mitad_same_products(self, sale_service, mock_uow, muzzarella_product, pizza_mitad_mitad_request):
        """Test validation when both products are the same."""
        # Use same product for both sides
        pizza_mitad_mitad_request.producto_id_derecha = 1  # Same as izquierda
        
        # Mock product repository
        mock_uow.product_repo.get_by_id.side_effect = [muzzarella_product, muzzarella_product]
        
        result = await sale_service._validate_pizza_mitad_mitad(pizza_mitad_mitad_request, mock_uow)
        
        assert result is not None
        assert result.status_code == 400
        assert "diferentes" in result.error

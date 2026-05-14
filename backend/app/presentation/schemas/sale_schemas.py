from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime, date
from typing import List, Optional


# ======================================================
# Query Parameters
# ======================================================

class SaleFilterParams(BaseModel):
    """Parámetros de filtrado para la lista de ventas."""
    skip: int = Field(0, ge=0, description="Número de registros a omitir")
    limit: int = Field(100, ge=1, le=1000, description="Límite de registros")
    fecha_desde: Optional[date] = Field(None, description="Fecha inicial del rango (YYYY-MM-DD)")
    fecha_hasta: Optional[date] = Field(None, description="Fecha final del rango (YYYY-MM-DD)")

# ======================================================
# Sale Items
# ======================================================

class SelectedProduct(BaseModel):
    """Producto seleccionado por el cliente al comprar una oferta."""
    producto_id: int = Field(..., gt=0, description="ID del producto seleccionado")
    cantidad: int = Field(..., gt=0, description="Cantidad de este producto en la oferta")


class PizzaMitadMitadRequest(BaseModel):
    """Configuración para pizza mitad-mitad."""
    producto_id_izquierda: int = Field(..., gt=0, description="ID del producto para el lado izquierdo")
    producto_id_derecha: int = Field(..., gt=0, description="ID del producto para el lado derecho")
    cantidad: int = Field(..., gt=0, le=100, description="Cantidad de pizzas mitad-mitad")

    @model_validator(mode="after")
    def validar_sabores_diferentes(self):
        if self.producto_id_izquierda == self.producto_id_derecha:
            raise ValueError("Los sabores deben ser diferentes")
        return self


class SaleItemRequest(BaseModel):
    producto_id: Optional[int] = Field(None, gt=0)
    oferta_id: Optional[int] = Field(None, gt=0)
    cantidad: int = Field(..., gt=0, le=1000, description="Cantidad a vender")
    precio_unitario: Optional[Decimal] = Field(None, gt=0, description="Precio unitario (opcional para updates)")
    productos_seleccionados: Optional[List[SelectedProduct]] = Field(
        None,
        description="Productos que el cliente eligió al comprar una oferta (solo si oferta_id está presente)"
    )
    pizza_mitad_mitad: Optional[PizzaMitadMitadRequest] = Field(
        None,
        description="Configuración para pizza mitad-mitad (exclusivo con producto_id y oferta_id)"
    )

    @model_validator(mode="after")
    def validar_tipos_mutuamente_exclusivos(self):
        # Validar que solo se especifique un tipo: producto, oferta, o pizza mitad-mitad
        tipos_especificados = sum([
            self.producto_id is not None,
            self.oferta_id is not None,
            self.pizza_mitad_mitad is not None
        ])
        
        if tipos_especificados == 0:
            raise ValueError("Debe especificar producto_id, oferta_id o pizza_mitad_mitad")
        if tipos_especificados > 1:
            raise ValueError("Solo se puede especificar uno de: producto_id, oferta_id, o pizza_mitad_mitad")
        
        # Validaciones específicas para cada tipo
        if self.oferta_id is not None:
            if not self.productos_seleccionados or len(self.productos_seleccionados) == 0:
                raise ValueError("Debe especificar productos_seleccionados al comprar una oferta")
        
        if self.producto_id is not None and self.productos_seleccionados:
            raise ValueError("No se puede especificar productos_seleccionados para un producto individual")
        
        if self.pizza_mitad_mitad is not None and self.productos_seleccionados:
            raise ValueError("No se puede especificar productos_seleccionados para pizza mitad-mitad")
        
        return self


class SaleItemResponse(BaseModel):
    id: int
    producto_id: Optional[int]
    oferta_id: Optional[int]
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    # Referencia de negocio - solo productos tienen SKU
    producto_sku: Optional[str] = None
    # Campos de snapshot (fuente de verdad histórica)
    item_nombre: str  # Nombre guardado al momento de la venta
    item_categoria: str  # Categoría al momento de la venta
    item_descripcion: Optional[str] = None  # Descripción de la oferta
    oferta_productos_snapshot: Optional[List["SaleItemOfferProductResponse"]] = None  # Productos de la oferta

    model_config = ConfigDict(from_attributes=True)


class SaleItemOfferProductResponse(BaseModel):
    """Snapshot de un producto incluido en una oferta vendida."""
    id: int
    producto_id: Optional[int]
    producto_nombre: str
    categoria_nombre: Optional[str]
    cantidad: int

    model_config = ConfigDict(from_attributes=True)


class SaleUpdateRequest(BaseModel):
    """Request para actualizar una venta existente.
    
    Nota: El número de orden es generado automáticamente y no puede ser editado.
    """
    items: List[SaleItemRequest] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validar_items(self):
        if not self.items or len(self.items) == 0:
            raise ValueError("La venta debe tener al menos un item")
        return self


# ======================================================
# Request Models
# ======================================================

class SaleCreateRequest(BaseModel):
    items: List[SaleItemRequest] = Field(..., min_length=1)
    aplicar_recargo: bool = Field(False, description="Aplicar recargo por pago en transferencia/débito")

    @model_validator(mode="after")
    def validar_items(self):
        if not self.items or len(self.items) == 0:
            raise ValueError("La venta debe tener al menos un item")
        return self


# ======================================================
# Response Models
# ======================================================

class SaleResponse(BaseModel):
    id: int
    numero_orden: str
    total: Decimal
    porcentaje_recargo: Optional[Decimal] = Field(None, description="Porcentaje de recargo aplicado")
    monto_recargo: Optional[Decimal] = Field(None, description="Monto de recargo aplicado")
    total_items: int = Field(0, description="Total de items (incluye productos dentro de ofertas)")
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    items: List[SaleItemResponse]

    model_config = ConfigDict(from_attributes=True)


class SaleListResponse(BaseModel):
    """Respuesta para la lista de ventas con paginación y filtros."""
    items: List[SaleResponse]
    total: int = Field(..., description="Total de ventas que coinciden con los filtros")
    skip: int = Field(..., ge=0, description="Número de registros omitidos")
    limit: int = Field(..., ge=1, description="Límite de registros por página")

    model_config = ConfigDict(from_attributes=True)

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


class SaleItemRequest(BaseModel):
    producto_id: Optional[int] = Field(None, gt=0)
    oferta_id: Optional[int] = Field(None, gt=0)
    cantidad: int = Field(..., gt=0, le=1000, description="Cantidad a vender")
    precio_unitario: Optional[Decimal] = Field(None, gt=0, description="Precio unitario (opcional para updates)")
    productos_seleccionados: Optional[List[SelectedProduct]] = Field(
        None,
        description="Productos que el cliente eligió al comprar una oferta (solo si oferta_id está presente)"
    )

    @model_validator(mode="after")
    def validar_producto_or_oferta(self):
        if self.producto_id is None and self.oferta_id is None:
            raise ValueError("Debe especificar producto_id o oferta_id")
        if self.producto_id is not None and self.oferta_id is not None:
            raise ValueError("No se puede especificar producto_id y oferta_id al mismo tiempo")
        
        # Si es una oferta, debe tener productos seleccionados
        if self.oferta_id is not None:
            if not self.productos_seleccionados or len(self.productos_seleccionados) == 0:
                raise ValueError("Debe especificar productos_seleccionados al comprar una oferta")
        
        # Si es un producto, no debe tener productos_seleccionados
        if self.producto_id is not None and self.productos_seleccionados:
            raise ValueError("No se puede especificar productos_seleccionados para un producto individual")
        
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

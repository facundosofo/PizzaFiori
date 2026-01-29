from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import List, Optional


# ======================================================
# Sale Items
# ======================================================

class SaleItemRequest(BaseModel):
    producto_id: Optional[int] = Field(None, gt=0)
    oferta_id: Optional[int] = Field(None, gt=0)
    cantidad: int = Field(..., gt=0, le=1000, description="Cantidad a vender")
    precio_unitario: Optional[Decimal] = Field(None, gt=0, description="Precio unitario (opcional para updates)")

    @model_validator(mode="after")
    def validar_producto_or_oferta(self):
        if self.producto_id is None and self.oferta_id is None:
            raise ValueError("Debe especificar producto_id o oferta_id")
        if self.producto_id is not None and self.oferta_id is not None:
            raise ValueError("No se puede especificar producto_id y oferta_id al mismo tiempo")
        return self


class SaleItemResponse(BaseModel):
    id: int
    producto_id: Optional[int]
    oferta_id: Optional[int]
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    producto_nombre: Optional[str] = None
    oferta_nombre: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SaleUpdateRequest(BaseModel):
    """Request para actualizar una venta existente."""
    numero_orden: Optional[str] = Field(None, max_length=50)
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
    numero_orden: Optional[str] = Field(None, max_length=50)
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
    numero_orden: Optional[str]
    total: Decimal
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    items: List[SaleItemResponse]

    model_config = ConfigDict(from_attributes=True)

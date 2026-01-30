from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import List, Optional


# ======================================================
# Offer Items
# ======================================================

class OfferItemRequest(BaseModel):
    producto_id: int = Field(..., gt=0, description="ID del producto")
    cantidad: int = Field(default=1, gt=0, le=100, description="Cantidad del producto en la oferta")


class OfferItemResponse(BaseModel):
    id: int
    producto_id: int
    cantidad: int
    producto_nombre: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ======================================================
# Request Models
# ======================================================

class OfferCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255, description="Nombre de la oferta")
    descripcion: Optional[str] = Field(None, max_length=1000, description="Descripción de la oferta")
    precio: Decimal = Field(..., gt=0, le=1_000_000, max_digits=10, decimal_places=2, description="Precio de la oferta")
    productos: List[OfferItemRequest] = Field(..., min_length=1, description="Lista de productos incluidos en la oferta")

    @model_validator(mode="after")
    def validar_productos(self):
        """Valida que no haya productos duplicados."""
        if not self.productos or len(self.productos) == 0:
            raise ValueError("La oferta debe tener al menos un producto")
        
        producto_ids = [p.producto_id for p in self.productos]
        
        if len(set(producto_ids)) != len(producto_ids):
            raise ValueError("No se permiten productos duplicados en la oferta")
        
        return self


class OfferUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None, max_length=1000)
    precio: Optional[Decimal] = Field(None, gt=0, le=1_000_000, max_digits=10, decimal_places=2)
    productos: Optional[List[OfferItemRequest]] = Field(None, min_length=1)

    @model_validator(mode="after")
    def validar_productos(self):
        """Valida que no haya productos duplicados si se proporcionan."""
        if self.productos is not None:
            if len(self.productos) == 0:
                raise ValueError("Si se proporcionan productos, debe haber al menos uno")
            
            producto_ids = [p.producto_id for p in self.productos]
            
            if len(set(producto_ids)) != len(producto_ids):
                raise ValueError("No se permiten productos duplicados en la oferta")
        
        return self


# ======================================================
# Response Models
# ======================================================

class OfferResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    precio: Decimal
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    productos: List[OfferItemResponse]
    
    model_config = ConfigDict(from_attributes=True)
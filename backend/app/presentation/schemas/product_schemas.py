from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import List, Optional


# ======================================================
# Precios escalonados
# ======================================================

class ProductoPrecioRequest(BaseModel):
    id: Optional[int] = None
    cantidad: int = Field(...,gt=0,le=1000,description="Cantidad mínima para aplicar el precio")
    precio: Decimal = Field(...,gt=0,le=1_000_000,max_digits=10, decimal_places=2,description="Precio para la cantidad indicada")

class ProductoPrecioResponse(BaseModel):
    id: int
    cantidad: int
    precio: Decimal

    class Config:
        model_config = ConfigDict(from_attributes=True)

# ======================================================
# Request Models
# ======================================================

class ProductoCreateRequest(BaseModel):
    nombre: str = Field(...,min_length=1,max_length=255)
    categoria_id: int = Field(..., gt=0)
    precios: List[ProductoPrecioRequest]

    @model_validator(mode="after")
    def validar_precios(self):
        if not self.precios or len(self.precios) == 0:
            raise ValueError("Debe existir al menos un precio") 

        cantidades = [p.cantidad for p in self.precios]

        if len(set(cantidades)) != len(cantidades):
            raise ValueError(
                "No se permiten cantidades duplicadas en precios"
            )

        return self
    


class ProductoUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(None,min_length=1,max_length=255)
    categoria_id: Optional[int] = Field(None, gt=0)
    precios: Optional[List[ProductoPrecioRequest]] = None
    activo: Optional[bool] = None
        
    @model_validator(mode="after")
    def validar_precios_update(self):
        if self.precios is not None:
            if len(self.precios) == 0:
                raise ValueError(
                    "La lista de precios no puede estar vacía"
                )

            cantidades = [p.cantidad for p in self.precios]

            if len(set(cantidades)) != len(cantidades):
                raise ValueError(
                    "No se permiten cantidades duplicadas en precios"
                )

        return self


# ======================================================
# Response Models
# ======================================================

class ProductoResponse(BaseModel):
    id: int
    nombre: str
    categoria_id: int
    precios: List[ProductoPrecioResponse]
    imagen: Optional[str] = None
    activo: bool
    fecha_creacion: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime


class AddStockRequest(BaseModel):
    cantidad: int = Field(..., description="Delta de stock (positivo = agregar, negativo = quitar)")

    @field_validator("cantidad")
    @classmethod
    def cantidad_no_cero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("La cantidad no puede ser 0")
        return v


class ConfigureAlertsRequest(BaseModel):
    umbral_amarillo: Optional[int] = Field(None, ge=0)
    umbral_rojo: Optional[int] = Field(None, ge=0)


class CategoryStockResponse(BaseModel):
    categoria_id: int
    categoria_nombre: str
    cantidad: int
    umbral_amarillo: Optional[int] = None
    umbral_rojo: Optional[int] = None
    estado: str  # "ok" | "warning" | "critical" | "sin_stock"


class StockMovementResponse(BaseModel):
    id: int
    timestamp: datetime
    username: str
    action: str
    changes: Any

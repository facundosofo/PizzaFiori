from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, datetime

from app.presentation.schemas.expense_category_schemas import GastoCategoriaResponse

# ---------------------------
# Request Models - Gasto
# ---------------------------
class GastoCreateRequest(BaseModel):
    categoria_gasto_id: int
    descripcion: Optional[str] = Field(None, max_length=255)
    monto: float = Field(..., gt=0)  # Greater than 0
    fecha_pago: date


class GastoUpdateRequest(BaseModel):
    categoria_gasto_id: Optional[int] = None
    descripcion: Optional[str] = Field(None, max_length=255)
    monto: Optional[float] = Field(None, gt=0)
    fecha_pago: Optional[date] = None


# ---------------------------
# Response Models - Gasto
# ---------------------------
class GastoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    categoria_gasto_id: int
    descripcion: Optional[str] = None
    monto: float
    fecha_pago: date
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime


class GastoDetailResponse(GastoResponse):
    """Response with nested category information"""
    categoria_gasto: Optional[GastoCategoriaResponse] = None

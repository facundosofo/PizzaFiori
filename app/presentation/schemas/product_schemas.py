from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ---------------------------
# Request Models
# ---------------------------
class ProductoCreateRequest(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio_venta: float

class ProductoUpdateRequest(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio_venta: Optional[float] = None
    activo: Optional[bool] = None

# ---------------------------
# Response Models
# ---------------------------
class ProductoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    precio_venta: float
    activo: bool
    fecha_creacion: datetime

class Config:
    orm_mode = True

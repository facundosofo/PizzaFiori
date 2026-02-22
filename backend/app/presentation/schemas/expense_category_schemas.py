from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

# ---------------------------
# Request Models - Categoria de Gastos
# ---------------------------
class GastoCategoriaCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=255)
    padre_id: Optional[int] = None


class GastoCategoriaUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=255)
    padre_id: Optional[int] = None


# ---------------------------
# Response Models - Categoria de Gastos
# ---------------------------
class GastoCategoriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: Optional[str] = None
    padre_id: Optional[int] = None
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime


class GastoCategoriaDetailResponse(GastoCategoriaResponse):
    """Response with nested subcategories"""
    subcategorias: List["GastoCategoriaResponse"] = Field(default_factory=list)


# Update forward refs
GastoCategoriaDetailResponse.model_rebuild()

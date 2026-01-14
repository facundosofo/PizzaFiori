from pydantic import BaseModel
from typing import Optional

# ---------------------------
# Request Models
# ---------------------------
class CategoriaCreateRequest(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class CategoriaUpdateRequest(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

# ---------------------------
# Response Models
# ---------------------------
class CategoriaResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None

    class Config:
        orm_mode = True

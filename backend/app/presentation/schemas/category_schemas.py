from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

# ---------------------------
# Request Models
# ---------------------------
class CategoriaCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50)
    descripcion: Optional[str] = None

class CategoriaUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=50)
    descripcion: Optional[str] = None

# ---------------------------
# Response Models
# ---------------------------
class CategoriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nombre: str
    descripcion: Optional[str] = None

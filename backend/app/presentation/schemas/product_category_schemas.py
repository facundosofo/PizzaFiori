from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

# ---------------------------
# Request Models
# ---------------------------
class ProductoCategoriaCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50)

class ProductoCategoriaUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=50)

# ---------------------------
# Response Models
# ---------------------------
class ProductoCategoriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    activo: bool

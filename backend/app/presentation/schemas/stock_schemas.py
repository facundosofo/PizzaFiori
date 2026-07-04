from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal


class AddStockRequest(BaseModel):
    cantidad: Decimal = Field(..., description="Delta de stock (positivo = agregar, negativo = quitar)")

    @field_validator("cantidad")
    @classmethod
    def cantidad_no_cero(cls, v: Decimal) -> Decimal:
        if v == 0:
            raise ValueError("La cantidad no puede ser 0")
        return v


class ConfigureAlertsRequest(BaseModel):
    umbral_amarillo: Optional[int] = Field(None, ge=0)
    umbral_rojo: Optional[int] = Field(None, ge=0)


class CategoryStockResponse(BaseModel):
    categoria_id: int
    categoria_nombre: str
    cantidad: float
    umbral_amarillo: Optional[int] = None
    umbral_rojo: Optional[int] = None
    estado: str  # "ok" | "warning" | "critical" | "sin_stock"
    stock_visible: bool = True
    stock_por_producto: bool = False
    num_productos: Optional[int] = None  # number of products when stock_por_producto=True


class StockListResponse(BaseModel):
    categorias: List[CategoryStockResponse]


class ProductStockResponse(BaseModel):
    producto_id: int
    producto_nombre: str
    cantidad: float
    umbral_amarillo: Optional[int] = None
    umbral_rojo: Optional[int] = None
    estado: str


class CategoryConfigItem(BaseModel):
    categoria_id: int
    stock_visible: bool
    stock_por_producto: bool


class SaveStockConfigRequest(BaseModel):
    configs: List[CategoryConfigItem]


class StockMovementResponse(BaseModel):
    id: int
    timestamp: datetime
    username: str
    action: str
    changes: Any


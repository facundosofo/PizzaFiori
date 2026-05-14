from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class RecargoConfigResponse(BaseModel):
    porcentaje_recargo: Decimal = Field(..., description="Porcentaje de recargo por transferencia/débito")

    model_config = ConfigDict(from_attributes=True)


class RecargoConfigUpdateRequest(BaseModel):
    porcentaje_recargo: Decimal = Field(..., ge=0, le=100, description="Porcentaje de recargo por transferencia/débito")

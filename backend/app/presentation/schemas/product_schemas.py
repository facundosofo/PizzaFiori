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
    precio: Decimal = Field(...,gt=0,le=99_999_999.99,max_digits=10, decimal_places=2,description="Precio para la cantidad indicada")

class ProductoPrecioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cantidad: int
    precio: Decimal

# ======================================================
# Request Models
# ======================================================

class ProductoCreateRequest(BaseModel):
    nombre: str = Field(...,min_length=1,max_length=50)
    categoria_id: int = Field(..., gt=0)
    precios: List[ProductoPrecioRequest]

    @model_validator(mode="after")
    def validar_precios(self):
        if not self.precios:
            raise ValueError("Debe existir al menos un precio")

        cantidades = [p.cantidad for p in self.precios]

        if len(set(cantidades)) != len(cantidades):
            raise ValueError("No se permiten cantidades duplicadas")

        if 1 not in cantidades:
            raise ValueError(
                "Debe existir un precio unitario"
            )

        return self

    


class ProductoUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(None,min_length=1,max_length=50)
    categoria_id: Optional[int] = Field(None, gt=0)
    precios: Optional[List[ProductoPrecioRequest]] = None
        
    @model_validator(mode="after")
    def validar_precios_update(self):
        if self.precios is not None:
            if not self.precios:
                raise ValueError("La lista de precios no puede estar vacía")

            cantidades = [p.cantidad for p in self.precios]

            if len(set(cantidades)) != len(cantidades):
                raise ValueError("No se permiten cantidades duplicadas")

            if 1 not in cantidades:
                raise ValueError(
                    "Debe existir un precio unitario"
                )

        return self



# ======================================================
# Response Models
# ======================================================

class ProductoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    sku: str
    nombre: str
    categoria_id: int
    precios: List[ProductoPrecioResponse]
    imagen: Optional[str] = None
    activo: bool
    fecha_creacion: datetime
    ofertas_desactivadas: Optional[List[int]] = None  # IDs de ofertas desactivadas al desactivar producto


# ======================================================
# Actualización masiva de precios
# ======================================================

class ActualizarPreciosMasivosRequest(BaseModel):
    monto: Optional[Decimal] = Field(
        None,
        description="Monto fijo a sumar o restar a cada precio (puede ser negativo)"
    )
    porcentaje: Optional[Decimal] = Field(
        None,
        description="Porcentaje a aumentar o disminuir (ej: 10 = +10%, -5 = -5%)"
    )
    categoria_ids: Optional[List[int]] = Field(
        None,
        description="Lista de IDs de categorías para filtrar. None = todos los productos activos"
    )

    @model_validator(mode="after")
    def validar_monto_o_porcentaje(self):
        if self.monto is None and self.porcentaje is None:
            raise ValueError("Debe especificar 'monto' o 'porcentaje'")
        if self.monto is not None and self.porcentaje is not None:
            raise ValueError("Solo puede especificar 'monto' o 'porcentaje', no ambos")
        if self.porcentaje is not None and self.porcentaje <= -100:
            raise ValueError("El porcentaje no puede ser -100% o menor")
        if self.categoria_ids is not None:
            if len(self.categoria_ids) == 0:
                raise ValueError("La lista de categorías no puede estar vacía")
            if any(cid <= 0 for cid in self.categoria_ids):
                raise ValueError("Todos los IDs de categoría deben ser mayores a 0")
        return self


class ActualizarPreciosMasivosResponse(BaseModel):
    productos_actualizados: int
    productos: List[ProductoResponse]

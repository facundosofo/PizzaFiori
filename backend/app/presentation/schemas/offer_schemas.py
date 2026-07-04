from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from datetime import datetime
from typing import List, Optional


# ======================================================
# Offer Items
# ======================================================

class OfferItemRequest(BaseModel):
    producto_id: Optional[int] = Field(None, gt=0, description="ID del producto")
    categoria_id: Optional[int] = Field(None, gt=0, description="ID de la categoría")
    producto_opciones: Optional[List[int]] = Field(None, min_length=2, description="Lista de IDs de productos alternativos (mínimo 2)")
    cantidad: Decimal = Field(
        default=Decimal("1"),
        gt=Decimal("0"),
        le=Decimal("1000"),
        multiple_of=Decimal("0.125"),
        description="Cantidad del item en la oferta (admite fracciones para producto/opciones)"
    )

    @model_validator(mode="after")
    def validar_tipo_item(self):
        """Valida que se proporcione exactamente uno de: producto_id, categoria_id, o producto_opciones."""
        campos_definidos = sum([
            self.producto_id is not None,
            self.categoria_id is not None,
            self.producto_opciones is not None
        ])
        
        if campos_definidos == 0:
            raise ValueError("Se debe proporcionar producto_id, categoria_id o producto_opciones")
        if campos_definidos > 1:
            raise ValueError("Solo se permite proporcionar uno de: producto_id, categoria_id o producto_opciones")
        
        # Validar que producto_opciones no tenga duplicados
        if self.producto_opciones is not None:
            if len(self.producto_opciones) != len(set(self.producto_opciones)):
                raise ValueError("La lista producto_opciones no puede contener IDs duplicados")

        # Las categorías no aceptan porciones: solo cantidades enteras.
        if self.categoria_id is not None and self.cantidad != int(self.cantidad):
            raise ValueError("Las categorías no permiten porciones")
        
        return self


class ProductoOpcionSchema(BaseModel):
    """Schema para productos en opciones múltiples."""
    id: int
    nombre: str
    imagen: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class OfferItemResponse(BaseModel):
    id: int
    categoria_id: Optional[int] = None
    cantidad: Decimal
    categoria_nombre: Optional[str] = None
    productos: Optional[List[ProductoOpcionSchema]] = None
    
    @field_validator('productos', mode='before')
    @classmethod
    def validate_productos(cls, v):
        """Convertir lista vacía a None para limpieza."""
        if v is not None and len(v) == 0:
            return None
        return v
    
    model_config = ConfigDict(from_attributes=True)


# ======================================================
# Request Models
# ======================================================

class OfferCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50, description="Nombre de la oferta")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripción de la oferta")
    precio: Decimal = Field(..., gt=0, le=99_999_999.99, max_digits=10, decimal_places=2, description="Precio de la oferta")
    productos: List[OfferItemRequest] = Field(..., min_length=1, description="Lista de productos incluidos en la oferta")

    @model_validator(mode="after")
    def validar_productos(self):
        """Valida que no haya items duplicados (producto/categoría/opciones)."""
        if not self.productos or len(self.productos) == 0:
            raise ValueError("La oferta debe tener al menos un producto")

        seen_items = []
        for item in self.productos:
            # Crear representación del item para comparar (sin cantidad)
            item_key = (
                item.producto_id,
                item.categoria_id,
                tuple(sorted(item.producto_opciones)) if item.producto_opciones else None,
            )
            
            if item_key in seen_items:
                if item.producto_id:
                    raise ValueError(f"Item duplicado: producto {item.producto_id}")
                elif item.categoria_id:
                    raise ValueError(f"Item duplicado: categoría {item.categoria_id}")
                elif item.producto_opciones:
                    raise ValueError(f"Item duplicado: opciones múltiples")
            
            seen_items.append(item_key)
        
        return self


class OfferUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=255)
    precio: Optional[Decimal] = Field(None, gt=0, le=99_999_999.99, max_digits=10, decimal_places=2)
    productos: Optional[List[OfferItemRequest]] = Field(None, min_length=1)

    @model_validator(mode="after")
    def validar_productos(self):
        """Valida que no haya items duplicados si se proporcionan (producto/categoría/opciones)."""
        if self.productos is not None:
            if len(self.productos) == 0:
                raise ValueError("Si se proporcionan productos, debe haber al menos uno")

            seen_items = []
            for item in self.productos:
                # Crear representación del item para comparar (sin cantidad)
                item_key = (
                    item.producto_id,
                    item.categoria_id,
                    tuple(sorted(item.producto_opciones)) if item.producto_opciones else None,
                )
                
                if item_key in seen_items:
                    if item.producto_id:
                        raise ValueError(f"Item duplicado: producto {item.producto_id}")
                    elif item.categoria_id:
                        raise ValueError(f"Item duplicado: categoría {item.categoria_id}")
                    elif item.producto_opciones:
                        raise ValueError(f"Item duplicado: opciones múltiples")
                
                seen_items.append(item_key)
        
        return self


# ======================================================
# Response Models
# ======================================================

class OfferResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    precio: Decimal
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    productos: List[OfferItemResponse]
    
    model_config = ConfigDict(from_attributes=True)
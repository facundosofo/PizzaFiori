from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PublicCatalogCategory(BaseModel):
    id: int
    nombre: str


class PublicCatalogPrice(BaseModel):
    cantidad: Decimal
    precio: Decimal


class PublicCatalogProduct(BaseModel):
    id: int
    nombre: str
    categoria_id: int
    imagen_url: Optional[str] = None
    precios: List[PublicCatalogPrice]


class PublicCatalogOfferItem(BaseModel):
    cantidad: Decimal
    categoria_id: Optional[int] = None
    producto_ids: List[int]


class PublicCatalogOffer(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    precio: Decimal
    items: List[PublicCatalogOfferItem]


class PublicCatalogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version: int = 1
    publicado_en: datetime
    categorias: List[PublicCatalogCategory]
    productos: List[PublicCatalogProduct]
    ofertas: List[PublicCatalogOffer]


class PublicCatalogCurrentPointer(BaseModel):
    version: int = 1
    catalogo_version: str
    publicado_en: datetime
    catalogo_url: str


class PublicCatalogPublishResponse(BaseModel):
    publicado_en: datetime
    catalogo_version: str
    catalogo_url: str
    categorias: int
    productos: int
    ofertas: int
    actualizado: bool


class PublicCatalogPublishStatus(BaseModel):
    publicado_en: Optional[datetime] = None

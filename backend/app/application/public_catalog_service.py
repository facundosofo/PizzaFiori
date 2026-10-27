import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from app.domain.models.offer import Offer
from app.domain.models.product import Product
from app.domain.models.product_category import ProductCategory
from app.domain.unit_of_work import AbstractUnitOfWork
from app.infrastructure.r2_catalog_storage import (
    CatalogStorageConfigurationError,
    CatalogStorageError,
    R2CatalogStorage,
    content_type_for_image,
)
from app.presentation.schemas.public_catalog_schemas import (
    PublicCatalogCategory,
    PublicCatalogOffer,
    PublicCatalogOfferItem,
    PublicCatalogPrice,
    PublicCatalogProduct,
    PublicCatalogCurrentPointer,
    PublicCatalogPublishResponse,
    PublicCatalogResponse,
)


logger = logging.getLogger(__name__)
CATALOG_PUBLISHED_AT_KEY = "public_catalog_published_at"
CATALOG_CONTENT_HASH_KEY = "public_catalog_content_hash"
CATALOG_VERSION_KEY = "public_catalog_version"
CATALOG_IMAGE_KEY_PREFIX = "public_catalog_image_"
RECARGO_KEY = "recargo_transferencia"
DEFAULT_RECARGO_PERCENTAGE = Decimal("10")


def build_public_catalog(
    categories: Sequence[ProductCategory],
    products: Sequence[Product],
    offers: Sequence[Offer],
    image_urls: Dict[int, str],
    published_at: datetime,
    porcentaje_recargo_transferencia: Decimal = DEFAULT_RECARGO_PERCENTAGE,
) -> PublicCatalogResponse:
    active_categories = {
        category.id: category
        for category in categories
        if category.activo
    }
    public_products = []
    product_ids = set()
    products_by_category: Dict[int, List[int]] = {}

    for product in products:
        if (
            not product.activo
            or product.categoria_id not in active_categories
            or not product.precios
        ):
            continue

        prices = sorted(product.precios, key=lambda price: price.cantidad)
        public_products.append(
            PublicCatalogProduct(
                id=product.id,
                nombre=product.nombre,
                categoria_id=product.categoria_id,
                imagen_url=image_urls.get(product.id),
                precios=[
                    PublicCatalogPrice(cantidad=price.cantidad, precio=price.precio)
                    for price in prices
                ],
            )
        )
        product_ids.add(product.id)
        products_by_category.setdefault(product.categoria_id, []).append(product.id)

    public_offers = []
    for offer in offers:
        if not offer.activo or not offer.productos:
            continue

        items = []
        valid_offer = True
        for item in offer.productos:
            if item.categoria_id is not None:
                if (
                    item.categoria_id not in active_categories
                    or not products_by_category.get(item.categoria_id)
                ):
                    valid_offer = False
                    break
                item_product_ids = []
            else:
                item_product_ids = sorted(
                    product.id for product in item.productos if product.id in product_ids
                )
                if not item_product_ids:
                    valid_offer = False
                    break

            items.append(
                PublicCatalogOfferItem(
                    cantidad=item.cantidad,
                    categoria_id=item.categoria_id,
                    producto_ids=item_product_ids,
                )
            )

        if valid_offer:
            public_offers.append(
                PublicCatalogOffer(
                    id=offer.id,
                    nombre=offer.nombre,
                    descripcion=offer.descripcion,
                    precio=offer.precio,
                    items=items,
                )
            )

    public_categories = [
        PublicCatalogCategory(id=category.id, nombre=category.nombre)
        for category in sorted(active_categories.values(), key=lambda value: value.id)
        if products_by_category.get(category.id)
    ]

    return PublicCatalogResponse(
        publicado_en=published_at,
        porcentaje_recargo_transferencia=porcentaje_recargo_transferencia,
        categorias=public_categories,
        productos=public_products,
        ofertas=public_offers,
    )


class PublicCatalogService:
    def __init__(
        self,
        storage: Optional[R2CatalogStorage] = None,
        uploads_root: Optional[Path] = None,
    ):
        self.storage = storage or R2CatalogStorage()
        self.uploads_root = (uploads_root or (Path.cwd() / "uploads")).resolve()

    async def publish(self, uow: AbstractUnitOfWork) -> PublicCatalogPublishResponse:
        self.storage.validate_configuration()

        categories = await uow.product_category_repo.list_by_active(activo=True)
        products = await uow.product_repo.list(active=True)
        offers = await uow.offer_repo.list(active=True)
        recargo_config = await uow.app_config_repo.get_by_key(RECARGO_KEY)
        porcentaje_recargo_transferencia = (
            Decimal(str(recargo_config.value))
            if recargo_config is not None
            else DEFAULT_RECARGO_PERCENTAGE
        )
        if (
            not porcentaje_recargo_transferencia.is_finite()
            or not Decimal("0") <= porcentaje_recargo_transferencia <= Decimal("100")
        ):
            raise ValueError("El porcentaje de recargo configurado debe estar entre 0 y 100.")
        published_at_config = await uow.app_config_repo.get_by_key(
            CATALOG_PUBLISHED_AT_KEY
        )
        content_hash_config = await uow.app_config_repo.get_by_key(
            CATALOG_CONTENT_HASH_KEY
        )
        version_config = await uow.app_config_repo.get_by_key(CATALOG_VERSION_KEY)
        active_category_ids = {category.id for category in categories}

        sellable_products = [
            product
            for product in products
            if product.categoria_id in active_category_ids and product.precios
        ]
        image_urls, image_objects = await self._prepare_images(sellable_products)
        published_at = datetime.now(timezone.utc)
        catalog = build_public_catalog(
            categories,
            products,
            offers,
            image_urls,
            published_at,
            porcentaje_recargo_transferencia,
        )
        content_hash = self._catalog_content_hash(catalog)
        previously_published_at = decode_publish_timestamp(
            published_at_config.value if published_at_config else None
        )
        if (
            content_hash_config
            and content_hash_config.value == content_hash
            and version_config
            and version_config.value
            and previously_published_at
        ):
            return PublicCatalogPublishResponse(
                publicado_en=previously_published_at,
                catalogo_version=version_config.value,
                catalogo_url=self.storage.object_url(
                    f"catalogo/{version_config.value}.json"
                ),
                categorias=len(catalog.categorias),
                productos=len(catalog.productos),
                ofertas=len(catalog.ofertas),
                actualizado=False,
            )

        catalog_json = catalog.model_dump_json(by_alias=True).encode("utf-8")
        catalog_version = hashlib.sha256(catalog_json).hexdigest()
        catalog_key = f"catalogo/{catalog_version}.json"
        catalog_url = self.storage.object_url(catalog_key)
        pointer_json = PublicCatalogCurrentPointer(
            catalogo_version=catalog_version,
            publicado_en=published_at,
            catalogo_url=catalog_url,
        ).model_dump_json(by_alias=True).encode("utf-8")

        images_to_upload = []
        for image in image_objects:
            image_config_key = self._image_config_key(image[1])
            if await uow.app_config_repo.get_by_key(image_config_key) is None:
                images_to_upload.append(image)

        await asyncio.to_thread(
            self.storage.publish,
            catalog_json,
            catalog_key,
            pointer_json,
            images_to_upload,
        )

        for _, object_key, _ in images_to_upload:
            await uow.app_config_repo.set_value(
                self._image_config_key(object_key),
                object_key,
            )
        await uow.app_config_repo.set_value(
            CATALOG_PUBLISHED_AT_KEY,
            published_at.isoformat(),
        )
        await uow.app_config_repo.set_value(CATALOG_CONTENT_HASH_KEY, content_hash)
        await uow.app_config_repo.set_value(CATALOG_VERSION_KEY, catalog_version)
        await uow.commit()

        return PublicCatalogPublishResponse(
            publicado_en=published_at,
            catalogo_version=catalog_version,
            catalogo_url=catalog_url,
            categorias=len(catalog.categorias),
            productos=len(catalog.productos),
            ofertas=len(catalog.ofertas),
            actualizado=True,
        )

    @staticmethod
    def _catalog_content_hash(catalog: PublicCatalogResponse) -> str:
        content = catalog.model_dump(
            mode="json",
            by_alias=True,
            exclude={"publicado_en"},
        )
        serialized_content = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(serialized_content).hexdigest()

    @staticmethod
    def _image_config_key(object_key: str) -> str:
        return f"{CATALOG_IMAGE_KEY_PREFIX}{Path(object_key).name}"

    async def _prepare_images(
        self,
        products: Sequence[Product],
    ) -> Tuple[Dict[int, str], List[Tuple[Path, str, str]]]:
        image_urls: Dict[int, str] = {}
        image_objects: List[Tuple[Path, str, str]] = []
        prepared_by_path: Dict[Path, Tuple[str, str]] = {}
        prepared_by_key: Dict[str, Tuple[Path, str]] = {}

        for product in products:
            if not product.imagen:
                continue

            image_path = self._resolve_image_path(product.imagen)
            if not image_path.is_file():
                raise FileNotFoundError(
                    f"No se encontró la imagen del producto {product.id}."
                )

            if image_path not in prepared_by_path:
                content_type = content_type_for_image(image_path)
                digest = await asyncio.to_thread(self._file_sha256, image_path)
                extension = ".jpg" if content_type == "image/jpeg" else ".png"
                object_key = f"catalogo/imagenes/{digest}{extension}"
                prepared_by_path[image_path] = (object_key, content_type)
                if object_key not in prepared_by_key:
                    prepared_by_key[object_key] = (image_path, content_type)
                    image_objects.append((image_path, object_key, content_type))

            object_key, _ = prepared_by_path[image_path]
            image_urls[product.id] = self.storage.object_url(object_key)

        return image_urls, image_objects

    def _resolve_image_path(self, stored_path: str) -> Path:
        image_path = Path(stored_path)
        if not image_path.is_absolute():
            image_path = Path.cwd() / image_path
        resolved_path = image_path.resolve()
        try:
            resolved_path.relative_to(self.uploads_root)
        except ValueError as exc:
            raise CatalogStorageError(
                "La ruta de imagen está fuera de la carpeta pública de uploads."
            ) from exc
        return resolved_path

    @staticmethod
    def _file_sha256(file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as image_file:
            for chunk in iter(lambda: image_file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


def decode_publish_timestamp(raw_value: Optional[str]) -> Optional[datetime]:
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(raw_value)
    except ValueError:
        logger.warning("La fecha de publicación del catálogo guardada no es válida.")
        return None

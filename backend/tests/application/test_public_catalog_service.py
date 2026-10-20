import asyncio
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.application.public_catalog_service import (
    PublicCatalogService,
    build_public_catalog,
)
from app.infrastructure.r2_catalog_storage import (
    CatalogStorageError,
    R2CatalogStorage,
)


def test_build_public_catalog_exposes_only_sellable_public_fields():
    active_category = SimpleNamespace(id=1, nombre="Pizzas", activo=True)
    inactive_category = SimpleNamespace(id=2, nombre="Oculta", activo=False)
    active_product = SimpleNamespace(
        id=10,
        nombre="Muzzarella",
        categoria_id=1,
        activo=True,
        imagen="uploads/productos/pizza.jpg",
        precios=[
            SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("12000")),
            SimpleNamespace(cantidad=Decimal("0.5"), precio=Decimal("6500")),
        ],
        sku="PRIVATE-SKU",
    )
    hidden_product = SimpleNamespace(
        id=11,
        nombre="No disponible",
        categoria_id=2,
        activo=True,
        imagen=None,
        precios=[SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("1"))],
    )
    product_without_price = SimpleNamespace(
        id=12,
        nombre="Sin precio",
        categoria_id=1,
        activo=True,
        imagen=None,
        precios=[],
    )
    offer = SimpleNamespace(
        id=20,
        nombre="Combo",
        descripcion="Oferta",
        precio=Decimal("15000"),
        activo=True,
        productos=[
            SimpleNamespace(
                cantidad=Decimal("1"),
                categoria_id=None,
                productos=[active_product],
            )
        ],
    )
    unpublished_offer = SimpleNamespace(
        id=21,
        nombre="Oferta no disponible",
        descripcion=None,
        precio=Decimal("100"),
        activo=True,
        productos=[
            SimpleNamespace(
                cantidad=Decimal("1"),
                categoria_id=None,
                productos=[hidden_product],
            )
        ],
    )
    published_at = datetime.now(timezone.utc)

    catalog = build_public_catalog(
        [active_category, inactive_category],
        [active_product, hidden_product, product_without_price],
        [offer, unpublished_offer],
        {10: "https://cdn.example.test/catalogo/imagenes/pizza.jpg"},
        published_at,
    )
    payload = catalog.model_dump(mode="json")

    assert payload["version"] == 1
    parsed_timestamp = datetime.fromisoformat(
        payload["publicado_en"].replace("Z", "+00:00")
    )
    assert parsed_timestamp == published_at
    assert [category["id"] for category in payload["categorias"]] == [1]
    assert [product["id"] for product in payload["productos"]] == [10]
    assert payload["productos"][0]["imagen_url"].endswith("pizza.jpg")
    assert [price["cantidad"] for price in payload["productos"][0]["precios"]] == [
        "0.5",
        "1",
    ]
    assert payload["ofertas"][0]["items"][0]["producto_ids"] == [10]
    assert len(payload["ofertas"]) == 1
    assert "sku" not in payload["productos"][0]


def test_build_public_catalog_keeps_public_products_without_images():
    category = SimpleNamespace(id=1, nombre="Empanadas", activo=True)
    product = SimpleNamespace(
        id=1,
        nombre="Carne",
        categoria_id=1,
        activo=True,
        imagen=None,
        precios=[SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("2000"))],
    )

    catalog = build_public_catalog(
        [category],
        [product],
        [],
        {},
        datetime.now(timezone.utc),
    )

    assert catalog.productos[0].imagen_url is None


def test_resolve_image_path_rejects_files_outside_uploads(tmp_path: Path):
    service = PublicCatalogService(uploads_root=tmp_path / "uploads")
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    image = uploads / "pizza.jpg"
    image.write_bytes(b"image")

    assert service._resolve_image_path(str(image)) == image.resolve()

    with pytest.raises(CatalogStorageError):
        service._resolve_image_path(str(tmp_path / "private.jpg"))


def test_r2_storage_uploads_images_before_public_catalog(tmp_path: Path, monkeypatch):
    config = SimpleNamespace(
        r2_enabled=True,
        r2_account_id="account",
        r2_access_key_id="access",
        r2_secret_access_key="secret",
        r2_bucket_name="catalog",
        r2_public_base_url="https://cdn.example.test",
    )
    image = tmp_path / "pizza.jpg"
    image.write_bytes(b"image")
    upload_order = []
    client = Mock()
    client.upload_file.side_effect = lambda *args, **kwargs: upload_order.append("image")
    client.put_object.side_effect = lambda **kwargs: upload_order.append(
        "pointer" if kwargs["Key"] == "catalogo-actual.json" else "catalog"
    )
    monkeypatch.setattr("boto3.client", lambda *args, **kwargs: client)

    storage = R2CatalogStorage(config)
    storage.publish(
        b'{"version":1}',
        "catalogo/hash.json",
        b'{"catalogo_version":"hash"}',
        [(image, "catalogo/imagenes/hash.jpg", "image/jpeg")],
    )

    assert upload_order == ["image", "catalog", "pointer"]
    catalog_upload, pointer_upload = client.put_object.call_args_list
    assert catalog_upload.kwargs["Key"] == "catalogo/hash.json"
    assert catalog_upload.kwargs["CacheControl"] == (
        "public, max-age=15552000, immutable"
    )
    assert pointer_upload.kwargs["Key"] == "catalogo-actual.json"
    assert pointer_upload.kwargs["CacheControl"] == (
        "no-cache, max-age=0, must-revalidate"
    )


def test_publish_points_to_content_hashed_catalog(tmp_path: Path):
    category = SimpleNamespace(id=1, nombre="Pizzas", activo=True)
    product = SimpleNamespace(
        id=10,
        nombre="Muzzarella",
        categoria_id=1,
        activo=True,
        imagen=None,
        precios=[SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("12000"))],
    )
    storage = Mock()
    storage.object_url.side_effect = lambda key: f"https://cdn.example.test/{key}"
    unit_of_work = SimpleNamespace(
        product_category_repo=SimpleNamespace(
            list_by_active=AsyncMock(return_value=[category])
        ),
        product_repo=SimpleNamespace(list=AsyncMock(return_value=[product])),
        offer_repo=SimpleNamespace(list=AsyncMock(return_value=[])),
        app_config_repo=SimpleNamespace(set_value=AsyncMock()),
        commit=AsyncMock(),
    )

    result = asyncio.run(
        PublicCatalogService(storage=storage, uploads_root=tmp_path).publish(unit_of_work)
    )

    catalog_json, catalog_key, pointer_json, images = storage.publish.call_args.args
    expected_hash = hashlib.sha256(catalog_json).hexdigest()
    pointer = json.loads(pointer_json)

    assert catalog_key == f"catalogo/{expected_hash}.json"
    assert pointer["catalogo_version"] == expected_hash
    assert pointer["catalogo_url"] == f"https://cdn.example.test/{catalog_key}"
    assert result.catalogo_version == expected_hash
    assert result.catalogo_url == pointer["catalogo_url"]
    assert images == []
    unit_of_work.app_config_repo.set_value.assert_awaited_once()
    unit_of_work.commit.assert_awaited_once()

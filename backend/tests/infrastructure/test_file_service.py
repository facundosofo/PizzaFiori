import io
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.infrastructure.file_service import FileService
import app.infrastructure.file_service as file_service_module


def _upload_file(filename: str, content_type: str, payload: bytes) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=io.BytesIO(payload),
        headers=Headers({"content-type": content_type}),
    )


class _DummySettings:
    # Local mode for these unit tests
    r2_enabled = False

    # Media limits (Cloudflare)
    media_max_image_bytes = 10 * 1024 * 1024
    media_max_image_megapixels = 25

    # R2 fields (unused in local tests)
    r2_endpoint_url = None
    r2_access_key_id = None
    r2_secret_access_key = None
    r2_bucket_name = None
    r2_public_base_url = None
    r2_key_prefix = "productos/"
    r2_max_ops_per_day = 500
    r2_max_total_bytes = 5 * 1024 * 1024 * 1024


class _DummyCache:
    def get(self, _key):
        return None

    def set(self, _key, _value):
        return None


class _DummyUowFactory:
    def __call__(self):
        raise RuntimeError("DB should not be used in local FileService tests")


def _service(tmp_path) -> FileService:
    return FileService(
        settings=_DummySettings(),
        cache_service=_DummyCache(),
        base_path=str(tmp_path),
    )


@pytest.mark.asyncio
async def test_save_file_rejects_invalid_extension(tmp_path, monkeypatch):
    monkeypatch.setattr(file_service_module, "_HAS_PIL", False)
    service = _service(tmp_path)
    upload = _upload_file("foto.gif", "image/png", b"123")

    with pytest.raises(HTTPException) as exc_info:
        await service.save_file(upload)

    assert exc_info.value.status_code == 400
    assert "Extensión no permitida" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_save_file_rejects_invalid_content_type(tmp_path, monkeypatch):
    monkeypatch.setattr(file_service_module, "_HAS_PIL", False)
    service = _service(tmp_path)
    upload = _upload_file("foto.png", "application/pdf", b"123")

    with pytest.raises(HTTPException) as exc_info:
        await service.save_file(upload)

    assert exc_info.value.status_code == 400
    assert "imagen válida" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_save_file_rejects_oversize(tmp_path, monkeypatch):
    monkeypatch.setattr(file_service_module, "_HAS_PIL", False)
    service = _service(tmp_path)
    payload = b"a" * (_DummySettings.media_max_image_bytes + 1)
    upload = _upload_file("foto.png", "image/png", payload)

    with pytest.raises(HTTPException) as exc_info:
        await service.save_file(upload)

    assert exc_info.value.status_code == 400
    assert "Archivo demasiado grande" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_save_file_rejects_over_megapixels(tmp_path, monkeypatch):
    PIL = pytest.importorskip("PIL")
    from PIL import Image

    monkeypatch.setattr(file_service_module, "_HAS_PIL", True)
    service = _service(tmp_path)

    # 6000x5000 = 30MP (limit is 25MP)
    img = Image.new("RGB", (6000, 5000), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    payload = buf.getvalue()

    upload = _upload_file("foto.png", "image/png", payload)

    with pytest.raises(HTTPException) as exc_info:
        await service.save_file(upload)

    assert exc_info.value.status_code == 400
    assert "máx 25MP" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_save_file_without_filename_base_generates_file_and_normalized_path(tmp_path, monkeypatch):
    monkeypatch.setattr(file_service_module, "_HAS_PIL", False)
    service = _service(tmp_path)
    payload = b"contenido-imagen"
    upload = _upload_file("foto.png", "image/png", payload)

    saved_path = await service.save_file(upload)

    assert saved_path.endswith(".png")
    assert "\\" not in saved_path
    saved_file = Path(saved_path)
    assert saved_file.exists()
    assert saved_file.read_bytes() == payload


@pytest.mark.asyncio
async def test_save_file_with_filename_base_uses_jpg_and_overwrites(tmp_path, monkeypatch):
    monkeypatch.setattr(file_service_module, "_HAS_PIL", False)
    service = _service(tmp_path)

    first = _upload_file("foto.png", "image/png", b"primero")
    second = _upload_file("foto.png", "image/png", b"segundo")

    first_path = await service.save_file(first, filename_base="SKU-001")
    second_path = await service.save_file(second, filename_base="SKU-001")

    assert first_path == second_path
    assert first_path.endswith("/SKU-001.jpg")
    assert Path(second_path).read_bytes() == b"segundo"


def test_delete_file_handles_empty_and_existing_path(tmp_path):
    service = _service(tmp_path)

    service.delete_file("")

    existing = tmp_path / "to-delete.jpg"
    existing.write_bytes(b"data")
    assert existing.exists()

    service.delete_file(str(existing))
    assert not existing.exists()


def test_delete_file_ignores_oserror(tmp_path, monkeypatch):
    service = _service(tmp_path)
    target = tmp_path / "locked.jpg"
    target.write_bytes(b"data")

    def _raise_oserror(*_args, **_kwargs):
        raise OSError("locked")

    monkeypatch.setattr(Path, "unlink", _raise_oserror)

    service.delete_file(str(target))
    assert target.exists()

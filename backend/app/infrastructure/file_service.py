from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional
from uuid import uuid4

import aiofiles
from fastapi import HTTPException, UploadFile
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.config.settings import Settings

try:
    from PIL import Image as _PIL_Image
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

_MAX_IMAGE_PX = 800  # Máximo lado en píxeles tras resize
_JPEG_QUALITY = 80   # Calidad JPEG (0-100)


@dataclass(frozen=True)
class FileSaveResult:
    url: str
    key: str
    size_bytes: int


class FileService:
    def __init__(
        self,
        settings: Settings,
        cache_service: CacheService,
        base_path: str = "uploads/productos",
    ):
        self.settings = settings
        self.cache = cache_service

        self.base_path = Path(base_path)
        self.allowed_extensions = {".jpg", ".jpeg", ".png"}
        self.r2_enabled = bool(getattr(settings, "r2_enabled", False))

        if not self.r2_enabled:
            self.base_path.mkdir(parents=True, exist_ok=True)

    def _validate_r2_config(self) -> None:
        if not self.settings.r2_endpoint_url:
            raise HTTPException(status_code=500, detail="R2_ENDPOINT_URL no configurado")
        if not self.settings.r2_access_key_id or not self.settings.r2_secret_access_key:
            raise HTTPException(status_code=500, detail="Credenciales de R2 no configuradas")
        if not self.settings.r2_bucket_name:
            raise HTTPException(status_code=500, detail="R2_BUCKET_NAME no configurado")
        if not self.settings.r2_public_base_url:
            raise HTTPException(status_code=500, detail="R2_PUBLIC_BASE_URL no configurado")

    def _r2_ops_key_today(self) -> str:
        return f"r2_ops_{date.today().isoformat()}"

    def _bump_ops_or_429(self) -> None:
        """Incrementa el contador diario de operaciones R2 (PUT/DELETE/etc)."""
        key = self._r2_ops_key_today()
        current = self.cache.get(key) or 0
        try:
            current_int = int(current)
        except Exception:
            current_int = 0

        if current_int >= self.settings.r2_max_ops_per_day:
            raise HTTPException(
                status_code=429,
                detail="Límite diario de operaciones de almacenamiento alcanzado. Intenta más tarde.",
            )
        self.cache.set(key, current_int + 1)

    async def _r2_head_size_bytes(self, key: str) -> Optional[int]:
        """Devuelve ContentLength del objeto o None si no existe."""
        import aioboto3

        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=self.settings.r2_endpoint_url,
            aws_access_key_id=self.settings.r2_access_key_id,
            aws_secret_access_key=self.settings.r2_secret_access_key,
            region_name="auto",
        ) as s3:
            try:
                self._bump_ops_or_429()
                resp = await s3.head_object(
                    Bucket=self.settings.r2_bucket_name,
                    Key=key,
                )
                return int(resp.get("ContentLength") or 0)
            except Exception:
                return None

    async def _r2_total_bytes_for_prefix(self) -> int:
        """Suma bytes del bucket/prefix consultando R2 (sin tocar BD)."""
        import aioboto3

        prefix = (self.settings.r2_key_prefix or "").lstrip("/")
        cache_key = f"r2_total_bytes:{prefix or '_all'}"
        cached = self.cache.get(cache_key)
        if isinstance(cached, dict) and "bytes" in cached and "ts" in cached:
            # Cache simple: recalcula solo cada 10 minutos
            try:
                age = (date.today().toordinal() - int(cached["ts"]))  # fallback coarse
            except Exception:
                age = 999
            if age == 0:
                try:
                    return int(cached["bytes"])
                except Exception:
                    pass

        total = 0
        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=self.settings.r2_endpoint_url,
            aws_access_key_id=self.settings.r2_access_key_id,
            aws_secret_access_key=self.settings.r2_secret_access_key,
            region_name="auto",
        ) as s3:
            continuation = None
            while True:
                self._bump_ops_or_429()
                kwargs = {"Bucket": self.settings.r2_bucket_name, "Prefix": prefix}
                if continuation:
                    kwargs["ContinuationToken"] = continuation
                resp = await s3.list_objects_v2(**kwargs)
                for obj in resp.get("Contents", []) or []:
                    total += int(obj.get("Size") or 0)
                if resp.get("IsTruncated"):
                    continuation = resp.get("NextContinuationToken")
                    if not continuation:
                        break
                else:
                    break

        # Guardar cache "por día" (TTL global 24h) para no listar en cada request.
        self.cache.set(cache_key, {"bytes": total, "ts": date.today().toordinal()})
        return total

    async def _enforce_storage_cap(self, key: str, new_size_bytes: int) -> None:
        cap = int(self.settings.r2_max_total_bytes)
        if cap <= 0:
            return

        # Si estamos sobreescribiendo, intentamos estimar el tamaño viejo con HEAD
        old_size = await self._r2_head_size_bytes(key) or 0
        total = await self._r2_total_bytes_for_prefix()
        projected = total - int(old_size) + int(new_size_bytes)
        if projected > cap:
            raise HTTPException(
                status_code=429,
                detail="Límite de almacenamiento alcanzado. Borra imágenes antes de subir nuevas.",
            )

    def _validate_image_bytes(self, size_bytes: int) -> None:
        if size_bytes > self.settings.media_max_image_bytes:
            mb = self.settings.media_max_image_bytes / (1024 * 1024)
            raise HTTPException(status_code=400, detail=f"Archivo demasiado grande (máx {mb:.0f}MB)")

    def _validate_image_megapixels(self, width: int, height: int) -> None:
        max_mp = int(self.settings.media_max_image_megapixels)
        if max_mp <= 0:
            return
        if width * height > max_mp * 1_000_000:
            raise HTTPException(
                status_code=400,
                detail=f"Imagen demasiado grande (máx {max_mp}MP)",
            )

    def _build_key(self, filename_base: Optional[str]) -> str:
        prefix = (self.settings.r2_key_prefix or "").strip()
        prefix = prefix.lstrip("/")
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        if filename_base:
            return f"{prefix}{filename_base}.jpg"
        return f"{prefix}{uuid4().hex}.jpg"

    def _public_url_for_key(self, key: str) -> str:
        base = (self.settings.r2_public_base_url or "").rstrip("/")
        return f"{base}/{key.lstrip('/')}"

    def _extract_key_from_url_or_key(self, value: str) -> str:
        base = (self.settings.r2_public_base_url or "").rstrip("/")
        if base and value.startswith(base):
            return value[len(base):].lstrip("/")
        return value.lstrip("/")

    async def save_image(
        self,
        file: UploadFile,
        filename_base: Optional[str] = None,
    ) -> FileSaveResult:
        # 1. Validar Extensión usando pathlib
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(status_code=400, detail="Extensión no permitida")

        # 2. Validar MIME Type (Doble seguridad)
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="El contenido no es una imagen válida")

        # 3. Leer contenido y validar tamaño (plan: 10MB max)
        contents = await file.read()
        self._validate_image_bytes(len(contents))

        # 3.5 Validar megapíxeles + redimensionar y comprimir con Pillow
        if _HAS_PIL:
            try:
                img = _PIL_Image.open(io.BytesIO(contents))
                self._validate_image_megapixels(img.width, img.height)
                # Convertir a RGB (descarta canal alfa y modos raros)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                # Reducir solo si supera el máximo; mantiene proporción
                if img.width > _MAX_IMAGE_PX or img.height > _MAX_IMAGE_PX:
                    img.thumbnail((_MAX_IMAGE_PX, _MAX_IMAGE_PX), _PIL_Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=_JPEG_QUALITY, optimize=True)
                contents = buf.getvalue()
                self._validate_image_bytes(len(contents))
            except Exception:
                pass  # Si Pillow falla, se sube el original sin redimensionar

        # 4. Guardar en R2 o en disco local según configuración
        if self.r2_enabled:
            self._validate_r2_config()
            key = self._build_key(filename_base)

            # Controles anti-cargo: ops + storage (antes del PUT)
            await self._enforce_storage_cap(key=key, new_size_bytes=len(contents))

            import aioboto3

            session = aioboto3.Session()
            async with session.client(
                "s3",
                endpoint_url=self.settings.r2_endpoint_url,
                aws_access_key_id=self.settings.r2_access_key_id,
                aws_secret_access_key=self.settings.r2_secret_access_key,
                region_name="auto",
            ) as s3:
                self._bump_ops_or_429()
                await s3.put_object(
                    Bucket=self.settings.r2_bucket_name,
                    Key=key,
                    Body=contents,
                    ContentType="image/jpeg",
                    CacheControl="public, max-age=3600",
                )

            return FileSaveResult(
                url=self._public_url_for_key(key),
                key=key,
                size_bytes=len(contents),
            )

        # Local fallback (dev / r2 disabled)
        if filename_base:
            filename = f"{filename_base}.jpg"
            file_path = self.base_path / filename
            mode = "wb"
        else:
            filename = f"{uuid4().hex}{file_ext}"
            file_path = self.base_path / filename
            mode = "xb"

        async with aiofiles.open(file_path, mode=mode) as f:
            await f.write(contents)

        url = str(file_path).replace("\\", "/")
        return FileSaveResult(url=url, key=url, size_bytes=len(contents))

    # Backward compatible name (used by ProductService historically)
    async def save_file(self, file: UploadFile, filename_base: Optional[str] = None) -> str:
        result = await self.save_image(file, filename_base=filename_base)
        return result.url

    async def delete_image(self, file_path_or_url_or_key: str) -> None:
        if not file_path_or_url_or_key:
            return

        # Local path legacy
        if file_path_or_url_or_key.startswith("uploads/") or file_path_or_url_or_key.startswith("uploads\\"):
            self._delete_local(file_path_or_url_or_key)
            return

        if self.r2_enabled:
            self._validate_r2_config()
            key = self._extract_key_from_url_or_key(file_path_or_url_or_key)

            self._bump_ops_or_429()

            import aioboto3

            session = aioboto3.Session()
            async with session.client(
                "s3",
                endpoint_url=self.settings.r2_endpoint_url,
                aws_access_key_id=self.settings.r2_access_key_id,
                aws_secret_access_key=self.settings.r2_secret_access_key,
                region_name="auto",
            ) as s3:
                await s3.delete_object(
                    Bucket=self.settings.r2_bucket_name,
                    Key=key,
                )
            return

        self._delete_local(file_path_or_url_or_key)

    def _delete_local(self, file_path: str) -> None:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
        except OSError as e:
            import logging

            logging.getLogger(__name__).warning(
                "No se pudo eliminar archivo: %s — %s", file_path, e
            )

    # Backward compatible name
    def delete_file(self, file_path: str) -> None:
        # This method is sync historically; keep best-effort for local paths.
        # For R2 we now use async delete_image from ProductService.
        if not file_path:
            return
        if file_path.startswith("uploads/") or file_path.startswith("uploads\\"):
            self._delete_local(file_path)
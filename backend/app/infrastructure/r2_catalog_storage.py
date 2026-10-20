import logging
import mimetypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Sequence, Tuple
from urllib.parse import urlparse

from app.infrastructure.config.settings import Settings, settings


logger = logging.getLogger(__name__)
CATALOG_MAX_AGE_SECONDS = 15_552_000
MAX_PARALLEL_IMAGE_UPLOADS = 4


class CatalogStorageConfigurationError(Exception):
    pass


class CatalogStorageError(Exception):
    pass


class R2CatalogStorage:
    def __init__(self, config: Settings = settings):
        self.config = config

    def object_url(self, key: str) -> str:
        base_url = self._public_base_url()
        return f"{base_url}/{key}"

    def _public_base_url(self) -> str:
        raw_url = self.config.r2_public_base_url
        if not raw_url:
            raise CatalogStorageConfigurationError(
                "Falta configurar R2_PUBLIC_BASE_URL."
            )
        parsed = urlparse(raw_url)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise CatalogStorageConfigurationError(
                "R2_PUBLIC_BASE_URL debe ser una URL HTTPS pública válida."
            )
        return raw_url.rstrip("/")

    def validate_configuration(self) -> None:
        if not self.config.r2_enabled:
            raise CatalogStorageConfigurationError(
                "La publicación en R2 está deshabilitada. Configure R2_ENABLED=true."
            )

        required = {
            "R2_ACCOUNT_ID": self.config.r2_account_id,
            "R2_ACCESS_KEY_ID": self.config.r2_access_key_id,
            "R2_SECRET_ACCESS_KEY": self.config.r2_secret_access_key,
            "R2_BUCKET_NAME": self.config.r2_bucket_name,
            "R2_PUBLIC_BASE_URL": self.config.r2_public_base_url,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise CatalogStorageConfigurationError(
                "Faltan variables de configuración de R2: " + ", ".join(missing)
            )
        self._public_base_url()

    def publish(
        self,
        catalog_json: bytes,
        catalog_key: str,
        current_pointer_json: bytes,
        images: Sequence[Tuple[Path, str, str]],
    ) -> None:
        self.validate_configuration()

        try:
            import boto3
            from botocore.config import Config
            from boto3.exceptions import S3UploadFailedError
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError as exc:
            logger.exception("No está disponible el cliente S3 requerido para R2.")
            raise CatalogStorageConfigurationError(
                "El servicio no tiene instalada la dependencia necesaria para R2."
            ) from exc

        try:
            client = boto3.client(
                "s3",
                endpoint_url=(
                    f"https://{self.config.r2_account_id}.r2.cloudflarestorage.com"
                ),
                aws_access_key_id=self.config.r2_access_key_id,
                aws_secret_access_key=self.config.r2_secret_access_key,
                region_name="auto",
                config=Config(signature_version="s3v4"),
            )

            if images:
                worker_count = min(MAX_PARALLEL_IMAGE_UPLOADS, len(images))
                with ThreadPoolExecutor(max_workers=worker_count) as executor:
                    uploads = [
                        executor.submit(
                            client.upload_file,
                            str(image_path),
                            self.config.r2_bucket_name,
                            object_key,
                            ExtraArgs={
                                "ContentType": content_type,
                                "CacheControl": (
                                    f"public, max-age={CATALOG_MAX_AGE_SECONDS}, immutable"
                                ),
                            },
                        )
                        for image_path, object_key, content_type in images
                    ]
                    for upload in as_completed(uploads):
                        upload.result()

            client.put_object(
                Bucket=self.config.r2_bucket_name,
                Key=catalog_key,
                Body=catalog_json,
                ContentType="application/json; charset=utf-8",
                CacheControl=(
                    f"public, max-age={CATALOG_MAX_AGE_SECONDS}, immutable"
                ),
            )

            client.put_object(
                Bucket=self.config.r2_bucket_name,
                Key="catalogo-actual.json",
                Body=current_pointer_json,
                ContentType="application/json; charset=utf-8",
                CacheControl="no-cache, max-age=0, must-revalidate",
            )
        except (BotoCoreError, ClientError, S3UploadFailedError) as exc:
            logger.exception("Falló la publicación del catálogo en R2.")
            raise CatalogStorageError(
                "No se pudo publicar el catálogo en Cloudflare R2."
            ) from exc


def content_type_for_image(image_path: Path) -> str:
    content_type, _ = mimetypes.guess_type(image_path.name)
    if content_type not in {"image/jpeg", "image/png"}:
        raise CatalogStorageError(
            f"Formato de imagen no admitido para publicar: {image_path.name}"
        )
    return content_type

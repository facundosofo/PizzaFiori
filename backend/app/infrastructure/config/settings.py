import sys as _sys
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, Dict
from pathlib import Path

# Resolve .env relative to the backend/ directory regardless of cwd.
# When running as a PyInstaller bundle (frozen), __file__ points inside the
# extraction temp dir; use sys.executable (the .exe) instead.
if getattr(_sys, 'frozen', False):
    # sys.executable = backend\dist\pizzafiori.exe  →  .parent.parent = backend\
    _BACKEND_DIR = Path(_sys.executable).resolve().parent.parent
else:
    _BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8"
    )
    
    app_name: str
    env: str
    debug: bool
    db_host: str
    db_name: str
    db_user: str
    db_password: str
    db_port: int
    api_port: int
    
    # Logging settings
    log_dir: str = "logs"
    log_file: str = "app.log"
    
    # JWT Configuration
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24h default
    jwt_refresh_token_expire_days: Optional[int] = 7  # Futuro: refresh tokens
    
    # Duraciones dinámicas por rol (minutos)
    jwt_token_durations: Dict[str, int] = Field(
        default={
            "ADMIN": 1 * 60,            # 1 horas
            "USER": 24 * 60,            # 24 horas
        }
    )
    
    # Password Policy
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_numbers: bool = True
    
    # Login Security
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 5
    rate_limit_window_seconds: int = 60
    
    # CORS
    cors_origins: str = Field(default="https://localhost:5173", alias="CORS_ORIGINS")

    # SSL/TLS Configuration
    ssl_key_file: Optional[str] = Field(default=None, alias="SSL_KEY_FILE")
    ssl_cert_file: Optional[str] = Field(default=None, alias="SSL_CERT_FILE")

    # Seed — credenciales del administrador inicial (leídas del .env)
    seed_admin_username: Optional[str] = Field(default=None, alias="SEED_ADMIN_USERNAME")
    seed_admin_email: Optional[str] = Field(default=None, alias="SEED_ADMIN_EMAIL")
    seed_admin_password: Optional[str] = Field(default=None, alias="SEED_ADMIN_PASSWORD")
    seed_admin_first_name: Optional[str] = Field(default=None, alias="SEED_ADMIN_FIRST_NAME")
    seed_admin_last_name: Optional[str] = Field(default=None, alias="SEED_ADMIN_LAST_NAME")

    # ---------------------------
    # Cloudflare R2 (S3 compatible)
    # ---------------------------
    r2_enabled: bool = Field(default=False, alias="R2_ENABLED")
    r2_endpoint_url: Optional[str] = Field(default=None, alias="R2_ENDPOINT_URL")
    r2_access_key_id: Optional[str] = Field(default=None, alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: Optional[str] = Field(default=None, alias="R2_SECRET_ACCESS_KEY")
    r2_bucket_name: Optional[str] = Field(default=None, alias="R2_BUCKET_NAME")

    # Public base URL used to serve objects (custom domain or public bucket URL)
    # Example: https://img.tudominio.com
    r2_public_base_url: Optional[str] = Field(default=None, alias="R2_PUBLIC_BASE_URL")
    r2_key_prefix: str = Field(default="productos/", alias="R2_KEY_PREFIX")

    # ---------------------------
    # Plan limits / cost controls
    # ---------------------------
    # R2 ops/day (PUT/DELETE/HEAD/LIST we issue). Default aligned with 500 admin API limit.
    r2_max_ops_per_day: int = Field(default=500, alias="R2_MAX_OPS_PER_DAY")
    # Total stored bytes cap (default 5GB). Used to prevent surprise costs.
    r2_max_total_bytes: int = Field(default=5 * 1024 * 1024 * 1024, alias="R2_MAX_TOTAL_BYTES")

    # Media constraints (Cloudflare plan)
    media_max_image_bytes: int = Field(default=10 * 1024 * 1024, alias="MEDIA_MAX_IMAGE_BYTES")  # 10MB
    media_max_raw_bytes: int = Field(default=10 * 1024 * 1024, alias="MEDIA_MAX_RAW_BYTES")      # 10MB
    media_max_image_megapixels: int = Field(default=25, alias="MEDIA_MAX_IMAGE_MEGAPIXELS")       # 25MP
    media_max_image_transform_bytes: int = Field(default=100 * 1024 * 1024, alias="MEDIA_MAX_IMAGE_TRANSFORM_BYTES")  # 100MB


settings = Settings()

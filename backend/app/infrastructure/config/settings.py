from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, Dict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    app_name: str
    env: str
    debug: bool
    db_host: str
    db_name: str
    db_driver: str
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
    
    # SSL/TLS Configuration
    ssl_key_file: Optional[str] = Field(default=None, alias="SSL_KEY_FILE")
    ssl_cert_file: Optional[str] = Field(default=None, alias="SSL_CERT_FILE")


settings = Settings()

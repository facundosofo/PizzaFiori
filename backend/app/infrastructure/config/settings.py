from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

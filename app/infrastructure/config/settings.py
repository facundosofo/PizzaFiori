from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str
    env: str
    debug: bool

    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_driver: str

    api_port: int

    class Config:
        env_file = ".env"


settings = Settings()

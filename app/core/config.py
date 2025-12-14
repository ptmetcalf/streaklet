from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_timezone: str = "America/Chicago"
    db_path: str = "/data/app.db"
    port: int = 8080

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

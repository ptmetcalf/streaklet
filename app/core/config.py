from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_timezone: str = "America/Chicago"
    db_path: str = "/data/app.db"
    port: int = 8080


settings = Settings()

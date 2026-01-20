from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_timezone: str = "America/Chicago"
    db_path: str = "/data/app.db"
    port: int = 8080

    # Fitbit OAuth
    fitbit_client_id: str = ""
    fitbit_client_secret: str = ""
    fitbit_callback_url: str = "http://localhost:8080/api/fitbit/callback"

    # Security
    app_secret_key: str = ""  # For token encryption (generate 32-byte random key)

    # Sync settings
    fitbit_sync_interval_hours: int = 1
    fitbit_backfill_days: int = 7


settings = Settings()

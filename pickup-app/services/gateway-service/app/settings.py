from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    auth_service_base_url: str = "http://auth-service:8001"
    pickups_service_base_url: str = "http://pickups-service:8002"

    cors_origins: str = "http://localhost:5173"


settings = Settings()  # type: ignore[call-arg]


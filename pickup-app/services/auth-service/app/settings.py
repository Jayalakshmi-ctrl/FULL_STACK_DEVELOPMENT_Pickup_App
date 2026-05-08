from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    jwt_secret: str
    jwt_issuer: str = "pickup-app"
    jwt_audience: str = "pickup-app-web"
    access_token_expire_minutes: int = 120

    admin_email: str = "admin@example.com"
    admin_password: str = "admin12345"

    vendor_email: str = "vendor@example.com"
    vendor_password: str = "vendor12345"

    cors_origins: str = "http://localhost:5173"


settings = Settings()  # type: ignore[call-arg]


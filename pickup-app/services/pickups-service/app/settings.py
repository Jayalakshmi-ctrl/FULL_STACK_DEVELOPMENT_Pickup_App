from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    jwt_secret: str
    jwt_issuer: str = "pickup-app"
    jwt_audience: str = "pickup-app-web"

    cors_origins: str = "http://localhost:5173"

    # Eco-Points: integer points awarded per 1 kg of verified plastic (vendor weigh-in).
    eco_points_per_kg: int = 100


settings = Settings()  # type: ignore[call-arg]


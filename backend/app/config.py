"""Application settings, loaded from environment variables / a .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "mysql+pymysql://listings_user:listings_pass@localhost:3306/listings_db?charset=utf8mb4"
    )
    # Comma separated list of origins allowed to call the API (the React dev server).
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

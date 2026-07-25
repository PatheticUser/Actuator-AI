from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

_INSECURE_DEFAULTS = {"dev-insecure-key-change-me", "", "changeme", "secret"}

class Settings(BaseSettings):
    PROJECT_NAME: str = "Actuator AI"
    API_V1_STR: str = "/api/v1"

    # Environment: "development" | "production"
    ENVIRONMENT: str = "development"

    # Security — dev fallback exists; production must set via env
    SECRET_KEY: str = "dev-insecure-key-change-me"

    @model_validator(mode="after")
    def _enforce_secret_key_in_production(self):
        if self.is_production and self.SECRET_KEY.lower() in _INSECURE_DEFAULTS:
            raise RuntimeError(
                "SECRET_KEY must be set to a secure value in production. "
                "Generate one with: openssl rand -hex 32"
            )
        return self

    # CORS — comma-separated origins, "*" for dev
    CORS_ORIGINS: str = "*"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "actuator_ai"
    POSTGRES_PORT: str = "5432"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def sql_echo(self) -> bool:
        return not self.is_production

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

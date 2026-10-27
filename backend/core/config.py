from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from urllib.parse import urlparse

_INSECURE_DEFAULTS = {"dev-insecure-key-change-me", "", "changeme", "secret"}

# Wording that appears in the tracked .env templates and in the usual
# "generate me" instructions (e.g. the .env.production.example value is
# "change … openssl rand …"). A production SECRET_KEY containing any of these
# is a placeholder copied straight from the repo, not a real secret — and a
# known signing key lets anyone forge session JWTs.
_SECRET_PLACEHOLDER_MARKERS = (
    "change",
    "example",
    "placeholder",
    "your-",
    "your_",
    "replace",
    "openssl",
    "generate",
    "changeme",
    "insecure",
)


def _is_insecure_secret(value: str) -> bool:
    """True when SECRET_KEY is empty, a known default, or template wording."""
    v = value.strip().lower()
    return v in _INSECURE_DEFAULTS or any(m in v for m in _SECRET_PLACEHOLDER_MARKERS)

# Loopback hosts are always trusted as an Origin: the local dev server (Vite on
# :5173) proxies to the backend, so the browser sends Origin=http://localhost:5173
# even though the request is same-origin from the page's point of view. A remote
# attacker cannot forge a browser Origin header, so this does not weaken
# cross-site WebSocket hijacking protection.
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "[::1]"}

class Settings(BaseSettings):
    PROJECT_NAME: str = "Actuator AI"
    API_V1_STR: str = "/api/v1"

    # Environment: "development" | "production"
    ENVIRONMENT: str = "development"

    # Security — dev fallback exists; production must set via env
    SECRET_KEY: str = "dev-insecure-key-change-me"

    @model_validator(mode="after")
    def _enforce_security_in_production(self):
        if self.is_production:
            if _is_insecure_secret(self.SECRET_KEY):
                raise RuntimeError(
                    "SECRET_KEY must be set to a secure value in production "
                    "(it is still the placeholder from .env.production.example). "
                    "Generate one with: openssl rand -hex 32"
                )
            if self.cors_origin_list == ["*"]:
                raise RuntimeError(
                    "CORS_ORIGINS must list explicit origins in production "
                    '(e.g. CORS_ORIGINS=https://your.domain). "*" combined with '
                    "allow_credentials=True leaks credentials."
                )
        return self

    # CORS — comma-separated origins, "*" for dev
    CORS_ORIGINS: str = "*"

    # Database
    DATABASE_URL: Optional[str] = None
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

    def is_allowed_origin(self, origin: str | None) -> bool:
        """Validate a browser Origin header (used by the WebSocket endpoint).

        CORSMiddleware never runs for WebSocket connections, so the origin has
        to be checked by hand. Requests without an Origin are allowed (native
        and server-side clients do not send one; browsers always do).
        """
        if not origin:
            return True
        if origin in self.cors_origin_list:
            return True
        return urlparse(origin).hostname in _LOOPBACK_HOSTS

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

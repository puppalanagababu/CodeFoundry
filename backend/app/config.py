import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "codefoundry-dev-fallback-key-only-for-local-testing"
    DEBUG: bool = False
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Database
    DATABASE_URL: Optional[str] = None
    DB_NAME: str = "codefoundry"
    DB_USER: str = "codefoundry_user"
    DB_PASSWORD: str = ""
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432

    # Redis & Celery
    REDIS_URL: str = "redis://127.0.0.1:6379/1"
    CELERY_BROKER_URL: str = "redis://127.0.0.1:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://127.0.0.1:6379/0"

    # Email
    DEFAULT_FROM_EMAIL: str = "noreply@codefoundry.dev"

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", BASE_DIR.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ALLOWED_ORIGINS:
            return ["http://localhost:5173", "http://127.0.0.1:5173"]
        origins = [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
        cleaned = [o for o in origins if o != "*"]
        return cleaned if cleaned else ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def allowed_hosts_list(self) -> List[str]:
        if not self.ALLOWED_HOSTS:
            return ["localhost", "127.0.0.1"]
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]

    def validate_production_configuration(self) -> List[str]:
        """
        Validates security and configuration readiness for production environments.
        Returns a list of error descriptions (empty if configuration is valid).
        """
        errors: List[str] = []
        is_prod = self.ENVIRONMENT.lower() in ["production", "prod"]

        if is_prod and not self.DEBUG:
            # 1. Secret Key validation
            insecure_keys = {
                "codefoundry-dev-fallback-key-only-for-local-testing",
                "your-production-secret-key-here-minimum-50-chars",
                "secret",
                "changeme",
            }
            if not self.SECRET_KEY or self.SECRET_KEY in insecure_keys:
                errors.append("SECRET_KEY must be set to a secure, unique production value and not use development defaults.")
            elif len(self.SECRET_KEY) < 32:
                errors.append("SECRET_KEY must be at least 32 characters long for production cryptographic security.")

            # 2. CORS validation
            raw_cors = [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
            if "*" in raw_cors:
                errors.append("CORS_ALLOWED_ORIGINS cannot contain wildcard '*' when allow_credentials=True in production.")

            # 3. Allowed Hosts validation
            if "*" in self.allowed_hosts_list:
                errors.append("ALLOWED_HOSTS cannot contain wildcard '*' in production.")

            # 4. Database password validation
            if not self.DATABASE_URL and not self.DB_PASSWORD:
                errors.append("Production database configuration requires a non-empty DB_PASSWORD or DATABASE_URL.")

        return errors

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            # Normalize postgres:// or postgresql:// to postgresql+psycopg2://
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url

        # Construct from individual DB_* environment variables with safe URL encoding
        import urllib.parse
        encoded_user = urllib.parse.quote_plus(self.DB_USER)
        encoded_password = urllib.parse.quote_plus(self.DB_PASSWORD) if self.DB_PASSWORD else ""
        password_part = f":{encoded_password}" if encoded_password else ""
        return f"postgresql+psycopg2://{encoded_user}{password_part}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()

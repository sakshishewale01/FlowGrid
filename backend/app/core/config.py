"""
Application Configuration
=========================
This module centralizes all configuration and environment variables for FlowGrid.

Why use Pydantic Settings?
--------------------------
1. Type Safety: Automatically parses environment variables into Python types (str, int, bool, list).
2. Default Values: Allows seamless local development without manually defining every variable.
3. Centralized Reference: Instead of scattered `os.getenv()` calls across the codebase,
   import `settings` from `app.core.config`.
4. Security: Credentials are read exclusively from environment variables / .env files,
   never hardcoded into source control.
"""

import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "flowgrid_super_secret_development_key_32_bytes_min_length_123!"


class Settings(BaseSettings):
    """
    Central application settings loaded securely from environment variables and/or .env file.
    """

    # Application details
    app_name: str = "FlowGrid"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Server binding
    host: str = "127.0.0.1"
    port: int = 8000

    # Cross-Origin Resource Sharing (CORS)
    allowed_origins: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Database Configuration (PostgreSQL + SQLAlchemy 2.0)
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/flowgrid_db"

    # Authentication & Security Configuration
    # In production, SECRET_KEY must be a cryptographically secure random string set in .env
    secret_key: str = DEFAULT_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    auth_rate_limit_requests: int = 60
    auth_rate_limit_window_seconds: int = 60

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("production", "prod")

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in ("development", "dev", "local", "test")

    def validate_runtime(self) -> None:
        """Validate configuration that is unsafe to infer in production."""
        if not self.is_production:
            return

        if self.debug:
            raise ValueError("DEBUG must be False when APP_ENV is production")
        if self.secret_key == DEFAULT_SECRET_KEY or len(self.secret_key) < 32:
            raise ValueError(
                "SECRET_KEY must be explicitly configured with at least 32 characters in production"
            )
        if self.database_url.startswith("sqlite"):
            raise ValueError("DATABASE_URL must reference PostgreSQL in production")
        if not self.allowed_origins or "*" in self.allowed_origins:
            raise ValueError("Production CORS origins must be explicit and restrictive")
        if any(
            origin.lower().startswith(("http://localhost", "http://127.0.0.1"))
            for origin in self.allowed_origins
        ):
            raise ValueError("Production CORS origins must not include local development hosts")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        """
        Parses allowed_origins whether supplied as a Python list, a JSON array string,
        or a comma-separated string in the .env file.
        """
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    return json.loads(value)
                except Exception:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, value: str) -> str:
        """
        Ensures the database URL is formatted with the modern psycopg (v3) dialect.
        If a standard postgresql:// or postgres:// URL is passed in .env,
        it is automatically adapted to postgresql+psycopg:// for SQLAlchemy 2.0.
        Also automatically sanitizes placeholder passwords left in .env.
        """
        if isinstance(value, str):
            value = value.strip()
            if "YOUR_STRONG_PASSWORD" in value:
                value = value.replace("YOUR_STRONG_PASSWORD", "postgres")
            if value.startswith("postgres://"):
                return value.replace("postgres://", "postgresql+psycopg://", 1)
            if value.startswith("postgresql://") and not value.startswith("postgresql+"):
                return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    # Configuration for loading .env files
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Instantiate a singleton settings object for use throughout the application
settings = Settings()

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


class Settings(BaseSettings):
    """
    Central application settings loaded securely from environment variables and/or .env file.
    """

    # Application details
    app_name: str = "FlowGrid"
    app_version: str = "0.4.0"
    app_env: str = "development"
    debug: bool = True

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

    # Authentication & Security Configuration (Phase 4)
    # In production, SECRET_KEY must be a cryptographically secure random string set in .env
    secret_key: str = "flowgrid_super_secret_development_key_32_bytes_min_length_123!"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

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
        """
        if isinstance(value, str):
            value = value.strip()
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

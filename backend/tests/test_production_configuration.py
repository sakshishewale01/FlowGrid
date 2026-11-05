import pytest

from app.core.config import DEFAULT_SECRET_KEY, Settings


def test_production_configuration_rejects_debug_mode():
    settings = Settings(
        _env_file=None,
        app_env="production",
        debug=True,
        secret_key="a" * 64,
        database_url="postgresql+psycopg://user:password@localhost/flowgrid",
        allowed_origins=["https://app.flowgrid.example"],
    )

    with pytest.raises(ValueError, match="DEBUG must be False"):
        settings.validate_runtime()


def test_production_configuration_rejects_default_secret():
    settings = Settings(
        _env_file=None,
        app_env="production",
        debug=False,
        secret_key=DEFAULT_SECRET_KEY,
        database_url="postgresql+psycopg://user:password@localhost/flowgrid",
        allowed_origins=["https://app.flowgrid.example"],
    )

    with pytest.raises(ValueError, match="SECRET_KEY"):
        settings.validate_runtime()


def test_production_configuration_requires_postgresql():
    settings = Settings(
        _env_file=None,
        app_env="production",
        debug=False,
        secret_key="a" * 64,
        database_url="sqlite:///flowgrid.db",
        allowed_origins=["https://app.flowgrid.example"],
    )

    with pytest.raises(ValueError, match="PostgreSQL"):
        settings.validate_runtime()


def test_valid_production_configuration_is_accepted():
    settings = Settings(
        _env_file=None,
        app_env="production",
        debug=False,
        secret_key="a" * 64,
        database_url="postgresql+psycopg://user:password@localhost/flowgrid",
        allowed_origins=["https://app.flowgrid.example"],
    )

    settings.validate_runtime()


def test_production_configuration_rejects_wildcard_cors():
    settings = Settings(
        _env_file=None,
        app_env="production",
        debug=False,
        secret_key="a" * 64,
        database_url="postgresql+psycopg://user:password@localhost/flowgrid",
        allowed_origins=["*"],
    )

    with pytest.raises(ValueError, match="CORS"):
        settings.validate_runtime()

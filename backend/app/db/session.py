"""
Database Engine and Session Management
======================================
Configures the synchronous SQLAlchemy 2.0 database engine, session factory,
and FastAPI request dependency.

Why use a Session Factory?
--------------------------
1. Connections: `engine` manages the physical pool of connections to PostgreSQL.
2. Sessions: `SessionLocal` creates isolated database transactions for each request.
3. Dependency Injection: `get_db()` provides a clean database session to FastAPI endpoints
   and guarantees it is properly closed when the HTTP response completes.
"""

from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("db")

# ------------------------------------------------------------------------------
# 1. SQLAlchemy Synchronous Engine with Intelligent Development Fallback
# ------------------------------------------------------------------------------
def _build_engine():
    db_url = settings.database_url
    if db_url.startswith("sqlite"):
        return create_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

    # For PostgreSQL: test connection with fast failover (3s timeout)
    try:
        pg_engine = create_engine(
            db_url,
            pool_pre_ping=True,
            echo=False,
            connect_args={"connect_timeout": 3},
        )
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Connected successfully to PostgreSQL database.")
        return pg_engine
    except Exception as exc:
        if settings.is_production:
            logger.error("PostgreSQL connection failed in production: %s", exc)
            raise RuntimeError(
                "PostgreSQL must be reachable when APP_ENV is production"
            ) from exc
        logger.warning(
            "PostgreSQL database connection failed (%s). "
            "Automatically falling back to local SQLite database (flowgrid_dev.db) for uninterrupted operation.",
            exc,
        )
        return create_engine(
            "sqlite:///flowgrid_dev.db",
            echo=False,
            connect_args={"check_same_thread": False},
        )

engine = _build_engine()

# ------------------------------------------------------------------------------
# 2. Session Factory
# ------------------------------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def ensure_db_tables_and_seed():
    """
    Ensures database tables exist and essential demo accounts are seeded.
    Called automatically on application startup.
    """
    try:
        from app.db.base import Base
        import app.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        from scripts.seed_demo_data import seed_demo_data
        seed_demo_data()
    except Exception as exc:
        logger.warning("Database schema check / seeding notice: %s", exc)


# ------------------------------------------------------------------------------
# 3. FastAPI Session Dependency
# ------------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding an open database session for a single request.
    Ensures the session is always closed in the `finally` block even if errors occur.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------------------
# 4. Safe Database Connectivity Test Helper
# ------------------------------------------------------------------------------
def check_db_connection() -> Tuple[bool, str]:
    """
    Executes a minimal test query ('SELECT 1') to verify whether the database
    is reachable and credentials are valid.

    Returns:
        (True, "Database connection successful") on success
        (False, error_description) on connection failure
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Database connection successful"
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}", exc_info=True)
        return False, f"Connection refused or database unreachable: {type(exc).__name__}"

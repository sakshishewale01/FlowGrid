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
# 1. SQLAlchemy Synchronous Engine
# ------------------------------------------------------------------------------
def _build_engine():
    db_url = settings.database_url
    if db_url.startswith("sqlite"):
        return create_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

    return create_engine(
        db_url,
        pool_pre_ping=True,
        echo=False,
        connect_args={"connect_timeout": 3},
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
    from app.db.base import Base
    import app.models  # noqa: F401

    with engine.connect() as connection:
        connection.execute(text("SELECT current_database()"))
    Base.metadata.create_all(bind=engine)
    from scripts.seed_demo_data import seed_demo_data
    seed_demo_data()


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
        logger.error(
            "Database health check failed: %s",
            type(exc).__name__,
        )
        return False, f"Connection refused or database unreachable: {type(exc).__name__}"

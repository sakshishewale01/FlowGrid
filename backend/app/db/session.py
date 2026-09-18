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

# ------------------------------------------------------------------------------
# 1. SQLAlchemy Synchronous Engine
# ------------------------------------------------------------------------------
# - pool_pre_ping=True: Validates connection health before issuing queries.
# - connect_args={"connect_timeout": 3}: Fails fast (3s) if PostgreSQL is offline
#   rather than blocking on operating system socket timeouts.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
    connect_args={"connect_timeout": 3},
)

# ------------------------------------------------------------------------------
# 2. Session Factory
# ------------------------------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


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
        return False, str(exc)

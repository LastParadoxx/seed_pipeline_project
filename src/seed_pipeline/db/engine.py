"""Database engine and session management.

This module centralises creation of the SQLAlchemy engine and session
factory.  The database URL is read from the `DATABASE_URL` environment
variable; if unset it defaults to a local Postgres instance as defined
in `docker-compose.yml`.

For most application code you should import `SessionLocal` to acquire a
session.  Use `with SessionLocal() as session:` to ensure the session
closes properly.
"""
from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


def get_database_url() -> str:
    """Return the database URL from the environment or a default.

    The default uses the same credentials as defined in docker-compose.yml.
    """
    return os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/seeddb",
    )


# Create engine and sessionmaker at import time.  Note: echo can be set via
# the environment to enable SQL logging when debugging.
_DATABASE_URL = get_database_url()
engine = create_engine(
    _DATABASE_URL,
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() in {"1", "true", "yes"},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


def get_session() -> Session:
    """Helper for dependency injection frameworks (e.g. FastAPI).

    Yields a new SQLAlchemy session and ensures it's closed after use.
    Usage:

        from seed_pipeline.db.engine import get_session

        with get_session() as session:
            # use session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
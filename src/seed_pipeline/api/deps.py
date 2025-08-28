"""FastAPI dependency functions."""
from __future__ import annotations

from typing import Generator

from fastapi import Depends

from ..db.engine import get_session


def get_db() -> Generator:
    """Yield a SQLAlchemy session for FastAPI dependency injection."""
    yield from get_session()
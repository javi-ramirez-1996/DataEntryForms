"""Database configuration for the backend service.

This module exposes a SQLAlchemy session factory configured for a
PostgreSQL database by default. The connection string can be
customised via the ``DATABASE_URL`` environment variable.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/dataentryforms",
)

# ``future=True`` enables SQLAlchemy 2.0 style usage while retaining 1.4 compatibility.
engine = create_engine(DATABASE_URL, future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)

Base = declarative_base()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations.

    Ensures that transactions are committed if everything succeeds, and rolled
    back on failure. Sessions are automatically closed afterwards.
    """

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

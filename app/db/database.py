"""
Database configuration and session management.
"""

import logging
from typing import Generator

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create database engine
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug,
    )
else:
    engine = create_engine(settings.database_url, echo=settings.debug)


def init_db() -> None:
    """Initialize database tables"""
    logger.info("Initializing database...")

    # Import models so they are registered with SQLModel metadata.
    import app.models.job_models  # noqa: F401
    import app.models.task_models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    logger.info("Database initialized successfully")


def get_session() -> Generator[Session, None, None]:
    """Get database session dependency"""
    session = Session(engine)
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()
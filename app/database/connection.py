"""
FinSight AI - Database Connection and Session Management
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from app.config import settings
from app.core.logger import logger

# SQLite needs check_same_thread=False
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
)

Base = declarative_base()

@contextmanager
def get_db_session():
    """Context manager for safe database transactions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session rollback due to error: {e}")
        raise
    finally:
        session.close()

def init_db():
    """Initialize database tables."""
    import app.database.models  # Ensure models are loaded
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")

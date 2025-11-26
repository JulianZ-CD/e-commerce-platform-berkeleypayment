"""
Database connection and session management.
Provides SQLAlchemy engine, session factory, and dependency injection for FastAPI.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings

# Create SQLAlchemy engine
# echo=True will log all SQL statements (useful for development)
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=10,  # Connection pool size
    max_overflow=20  # Allow up to 20 additional connections
)

# Create session factory
# autocommit=False: Transactions must be explicitly committed
# autoflush=False: Don't automatically flush before queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI endpoints.
    
    Usage in route:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    
    Yields:
        Session: SQLAlchemy database session
        
    The session is automatically closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


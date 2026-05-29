"""
Database Base — SQLAlchemy engine, session factory, Base model
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite için gerekli
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — veritabanı session'ı sağlar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Tüm tabloları oluşturur."""
    from app.database import db_models  # noqa: F401 — modelleri kaydet
    Base.metadata.create_all(bind=engine)

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
    """Tüm tabloları oluşturur ve eksik kolonları mevcut tablolara ekler."""
    from app.database import db_models  # noqa: F401 — modelleri kaydet
    Base.metadata.create_all(bind=engine)
    _migrate_missing_columns()


def _migrate_missing_columns():
    """SQLite create_all() var olan tabloları değiştirmez — eksik kolonları ALTER TABLE ile ekler."""
    from sqlalchemy import inspect, text

    jobs_columns = {
        "is_favorite": "ALTER TABLE jobs ADD COLUMN is_favorite BOOLEAN DEFAULT 0",
        "style": "ALTER TABLE jobs ADD COLUMN style VARCHAR DEFAULT 'realistic'",
        "enhanced_prompt": "ALTER TABLE jobs ADD COLUMN enhanced_prompt VARCHAR",
    }

    inspector = inspect(engine)
    if "jobs" not in inspector.get_table_names():
        return
    existing_columns = {col["name"] for col in inspector.get_columns("jobs")}
    with engine.connect() as conn:
        for column, ddl in jobs_columns.items():
            if column not in existing_columns:
                conn.execute(text(ddl))
        conn.commit()

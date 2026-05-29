"""
Database Store — SQLite tabanlı job deposu.
memory_store.py'nin yerini alır.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import JobStatus
from app.database.base import SessionLocal
from app.database.db_models import JobDB
from app.models.job_model import JobModel

logger = logging.getLogger(__name__)


def _db_to_model(job_db: JobDB) -> JobModel:
    """JobDB → JobModel dönüşümü."""
    job = JobModel(
        id=job_db.id,
        prompt=job_db.prompt,
        backend=job_db.backend,
        output_format=job_db.output_format,
        num_steps=job_db.num_steps,
        guidance_scale=job_db.guidance_scale,
        mesh_resolution=job_db.mesh_resolution,
    )
    job.status = job_db.status
    job.progress = job_db.progress
    job.current_stage = job_db.current_stage
    job.output_path = job_db.output_path
    job.output_url = job_db.output_url
    job.error_message = job_db.error_message
    job.metadata = job_db.job_metadata or {}
    job.created_at = job_db.created_at
    job.updated_at = job_db.updated_at
    job.completed_at = job_db.completed_at
    job.duration_seconds = job_db.duration_seconds
    return job


def _model_to_db_dict(job: JobModel) -> dict:
    """JobModel → JobDB güncelleme dict'i."""
    return {
        "status": job.status,
        "progress": job.progress,
        "current_stage": job.current_stage,
        "output_path": job.output_path,
        "output_url": job.output_url,
        "error_message": job.error_message,
        "job_metadata": job.metadata,
        "updated_at": job.updated_at,
        "completed_at": job.completed_at,
        "duration_seconds": job.duration_seconds,
        "output_format": job.output_format,
    }


class DatabaseStore:
    """SQLite tabanlı job deposu."""

    def initialize(self) -> None:
        from app.database.base import init_db
        init_db()
        logger.info("Database initialized")

    def clear_all(self) -> None:
        pass  # Production'da verileri silmiyoruz

    def save(self, job: JobModel, user_id: str | None = None) -> None:
        with SessionLocal() as db:
            existing = db.query(JobDB).filter(JobDB.id == job.id).first()
            if existing:
                for key, value in _model_to_db_dict(job).items():
                    setattr(existing, key, value)
            else:
                job_db = JobDB(
                    id=job.id,
                    user_id=user_id,
                    prompt=job.prompt,
                    backend=job.backend,
                    output_format=job.output_format,
                    num_steps=job.num_steps,
                    guidance_scale=job.guidance_scale,
                    mesh_resolution=job.mesh_resolution,
                    status=job.status,
                    progress=job.progress,
                    current_stage=job.current_stage,
                    output_path=job.output_path,
                    output_url=job.output_url,
                    error_message=job.error_message,
                    job_metadata=job.metadata,
                    created_at=job.created_at,
                    updated_at=job.updated_at,
                    completed_at=job.completed_at,
                    duration_seconds=job.duration_seconds,
                )
                db.add(job_db)
            db.commit()

    def get(self, job_id: str) -> Optional[JobModel]:
        with SessionLocal() as db:
            job_db = db.query(JobDB).filter(JobDB.id == job_id).first()
            if not job_db:
                return None
            return _db_to_model(job_db)

    def delete(self, job_id: str) -> bool:
        with SessionLocal() as db:
            job_db = db.query(JobDB).filter(JobDB.id == job_id).first()
            if not job_db:
                return False
            db.delete(job_db)
            db.commit()
            return True

    def all(self, user_id: str | None = None) -> list[JobModel]:
        with SessionLocal() as db:
            query = db.query(JobDB)
            if user_id:
                query = query.filter(JobDB.user_id == user_id)
            jobs = query.order_by(JobDB.created_at.desc()).all()
            return [_db_to_model(j) for j in jobs]

    def count(self, user_id: str | None = None) -> int:
        with SessionLocal() as db:
            query = db.query(JobDB)
            if user_id:
                query = query.filter(JobDB.user_id == user_id)
            return query.count()

    def exists(self, job_id: str) -> bool:
        with SessionLocal() as db:
            return db.query(JobDB).filter(JobDB.id == job_id).count() > 0

    def filter_by_status(self, status: str, user_id: str | None = None) -> list[JobModel]:
        with SessionLocal() as db:
            query = db.query(JobDB).filter(JobDB.status == status)
            if user_id:
                query = query.filter(JobDB.user_id == user_id)
            return [_db_to_model(j) for j in query.all()]

    def count_by_status(self, user_id: str | None = None) -> dict[str, int]:
        jobs = self.all(user_id=user_id)
        counts: dict[str, int] = {}
        for job in jobs:
            counts[job.status] = counts.get(job.status, 0) + 1
        return counts


# Global singleton — memory_store'un yerini alır
store = DatabaseStore()

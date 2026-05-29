"""
In-Memory Job Store — thread-safe dictionary-backed storage.
Replace with Redis / SQLite adapter in production.
"""

import threading
from typing import Optional

from app.models.job_model import JobModel


class MemoryStore:
    """Thread-safe in-memory store for JobModel objects."""

    def __init__(self) -> None:
        self._store: dict[str, JobModel] = {}
        self._lock = threading.RLock()
        self._initialized = False

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def initialize(self) -> None:
        with self._lock:
            self._store.clear()
            self._initialized = True

    def clear_all(self) -> None:
        with self._lock:
            self._store.clear()

    # ── CRUD ──────────────────────────────────────────────────────────────

    def save(self, job: JobModel) -> None:
        with self._lock:
            self._store[job.id] = job

    def get(self, job_id: str) -> Optional[JobModel]:
        with self._lock:
            return self._store.get(job_id)

    def delete(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._store:
                del self._store[job_id]
                return True
            return False

    def all(self) -> list[JobModel]:
        with self._lock:
            return list(self._store.values())

    def count(self) -> int:
        with self._lock:
            return len(self._store)

    def exists(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._store

    # ── Filters ───────────────────────────────────────────────────────────

    def filter_by_status(self, status: str) -> list[JobModel]:
        with self._lock:
            return [j for j in self._store.values() if j.status == status]

    def count_by_status(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for job in self._store.values():
                counts[job.status] = counts.get(job.status, 0) + 1
            return counts


# Global singleton
store = MemoryStore()

"""
Internal Job Model
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.core.constants import JobStatus


@dataclass
class JobModel:
    id: str
    prompt: str
    backend: str
    output_format: str
    num_steps: int
    guidance_scale: float
    mesh_resolution: int
    enhanced_prompt: Optional[str] = None
    style: str = "realistic"

    status: str = JobStatus.PENDING
    progress: int = 0
    current_stage: Optional[str] = None
    output_path: Optional[str] = None
    output_url: Optional[str] = None
    error_message: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_running(self, stage: str) -> None:
        self.status = JobStatus.RUNNING
        self.current_stage = stage
        self.updated_at = datetime.utcnow()

    def update_progress(self, progress: int, stage: Optional[str] = None) -> None:
        self.progress = min(progress, 100)
        if stage:
            self.current_stage = stage
        self.updated_at = datetime.utcnow()

    def mark_completed(self, output_path: str, output_url: str) -> None:
        self.status = JobStatus.COMPLETED
        self.progress = 100
        self.output_path = output_path
        self.output_url = output_url
        self.completed_at = datetime.utcnow()
        self.updated_at = self.completed_at
        self.duration_seconds = (self.completed_at - self.created_at).total_seconds()

    def mark_failed(self, error: str) -> None:
        self.status = JobStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.utcnow()
        self.updated_at = self.completed_at
        self.duration_seconds = (self.completed_at - self.created_at).total_seconds()

    def mark_cancelled(self) -> None:
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = self.completed_at

    @property
    def is_terminal(self) -> bool:
        return self.status in JobStatus.TERMINAL

    @property
    def active_prompt(self) -> str:
        """Pipeline'a gönderilecek prompt — enhanced varsa onu kullan."""
        return self.enhanced_prompt or self.prompt

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "enhanced_prompt": self.enhanced_prompt,
            "style": self.style,
            "backend": self.backend,
            "output_format": self.output_format,
            "num_steps": self.num_steps,
            "guidance_scale": self.guidance_scale,
            "mesh_resolution": self.mesh_resolution,
            "status": self.status,
            "progress": self.progress,
            "current_stage": self.current_stage,
            "output_path": self.output_path,
            "output_url": self.output_url,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
        }

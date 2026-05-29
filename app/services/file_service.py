"""
File Service — manages output directory and generated 3D files.
"""

from pathlib import Path
from app.core.config import settings


class FileService:
    def __init__(self) -> None:
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_output_path(self, job_id: str, fmt: str) -> Path:
        return self.output_dir / f"{job_id}.{fmt}"

    def file_exists(self, path: str) -> bool:
        return Path(path).exists()

    def get_file_size(self, path: str) -> int | None:
        p = Path(path)
        return p.stat().st_size if p.exists() else None

    def delete_file(self, path: str) -> bool:
        p = Path(path)
        if p.exists():
            p.unlink()
            return True
        return False
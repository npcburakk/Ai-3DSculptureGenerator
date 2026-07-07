"""
File Service — manages output directory and generated 3D files.
"""

import base64
import mimetypes
import shutil
from pathlib import Path
from app.core.config import settings


class FileService:
    def __init__(self) -> None:
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

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

    def save_uploaded_images(self, job_id: str, images: list[tuple[bytes, str]]) -> list[Path]:
        """Yüklenen fotoğrafları uploads/{job_id}/ altına kaydeder, kaydedilen yolları döner."""
        job_dir = self.upload_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i, (content, filename) in enumerate(images):
            ext = Path(filename).suffix.lower()
            if ext not in (".jpg", ".jpeg", ".png"):
                ext = ".jpg"
            path = job_dir / f"{i}{ext}"
            path.write_bytes(content)
            paths.append(path)
        return paths

    def copy_uploaded_images(self, source_paths: list[str], new_job_id: str) -> list[str]:
        """Var olan yüklenen fotoğrafları yeni bir job_id klasörüne kopyalar (retry için)."""
        if not source_paths:
            return []
        job_dir = self.upload_dir / new_job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        new_paths = []
        for i, source in enumerate(source_paths):
            src = Path(source)
            if not src.exists():
                continue
            dest = job_dir / f"{i}{src.suffix}"
            dest.write_bytes(src.read_bytes())
            new_paths.append(str(dest))
        return new_paths

    def delete_upload_dir(self, job_id: str) -> None:
        """Job'a ait yüklenen fotoğraf klasörünü (varsa) diskten siler."""
        job_dir = self.upload_dir / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)

    def image_to_data_uri(self, path: Path) -> str:
        mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
"""
Job Service
"""

import logging
import uuid
from typing import Optional

from app.core.constants import JobStatus
from app.models.job_model import JobModel
from app.schemas.job_schema import JobCreateRequest, JobResponse, JobListResponse, PostProcessingOptions
from app.services.pipeline_service import PipelineService
from app.services.file_service import FileService
from app.database.db_store import store
from app.utils.error_messages import to_user_message

logger = logging.getLogger(__name__)
pipeline = PipelineService()
file_service = FileService()


class JobService:

    def create_job(self, payload: JobCreateRequest, user_id=None, enhanced_prompt=None) -> JobResponse:
        job = JobModel(
            id=str(uuid.uuid4()),
            prompt=payload.prompt,
            enhanced_prompt=enhanced_prompt,
            style=payload.style,
            backend=payload.backend,
            output_format=payload.output_format,
            num_steps=payload.num_steps,
            guidance_scale=payload.guidance_scale,
            mesh_resolution=payload.mesh_resolution,
        )
        # Post-processing ayarlarını metadata'ya ekle
        job.metadata["post_processing"] = payload.post_processing.model_dump()
        store.save(job, user_id=user_id)
        logger.info(f"[{job.id}] Job created | prompt='{job.prompt}'")
        return JobResponse(**job.to_dict())

    def create_image_job(
        self, images: list[tuple[bytes, str]], style: str, output_format: str, user_id=None
    ) -> JobResponse:
        job_id = str(uuid.uuid4())
        image_paths = file_service.save_uploaded_images(job_id, images)
        job = JobModel(
            id=job_id,
            prompt=f"Fotoğraftan büst ({len(images)} fotoğraf)",
            style=style,
            backend="meshy",
            output_format=output_format,
            num_steps=64,
            guidance_scale=15.0,
            mesh_resolution=128,
        )
        job.metadata["job_type"] = "image_bust"
        job.metadata["image_paths"] = [str(p) for p in image_paths]
        job.metadata["post_processing"] = PostProcessingOptions().model_dump()
        store.save(job, user_id=user_id)
        logger.info(f"[{job.id}] Image job created | {len(images)} photo(s)")
        return JobResponse(**job.to_dict())

    def retry_job(self, job_id: str, user_id=None) -> JobResponse:
        """Başarısız bir job'ın parametrelerini aynen kullanarak yeni bir job oluşturur."""
        job = store.get(job_id)
        new_job = JobModel(
            id=str(uuid.uuid4()),
            prompt=job.prompt,
            enhanced_prompt=job.enhanced_prompt,
            style=job.style,
            backend=job.backend,
            output_format=job.output_format,
            num_steps=job.num_steps,
            guidance_scale=job.guidance_scale,
            mesh_resolution=job.mesh_resolution,
        )
        if job.metadata.get("job_type") == "image_bust":
            new_paths = file_service.copy_uploaded_images(
                job.metadata.get("image_paths", []), new_job.id
            )
            new_job.metadata["job_type"] = "image_bust"
            new_job.metadata["image_paths"] = new_paths
        new_job.metadata["post_processing"] = job.metadata.get(
            "post_processing", PostProcessingOptions().model_dump()
        )
        new_job.metadata["retry_of"] = job_id
        store.save(new_job, user_id=user_id)
        logger.info(f"[{new_job.id}] Retry of [{job_id}] created")
        return JobResponse(**new_job.to_dict())

    def get_job(self, job_id: str):
        job = store.get(job_id)
        return JobResponse(**job.to_dict()) if job else None

    def list_jobs(self, page=1, page_size=10, status_filter=None, user_id=None) -> JobListResponse:
        jobs = store.all(user_id=user_id)
        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]
        total = len(jobs)
        start = (page - 1) * page_size
        page_jobs = jobs[start:start + page_size]
        return JobListResponse(total=total, page=page, page_size=page_size,
            jobs=[JobResponse(**j.to_dict()) for j in page_jobs])

    def toggle_favorite(self, job_id: str):
        job = store.get(job_id)
        if not job:
            return None
        job.toggle_favorite()
        store.save(job)
        return JobResponse(**job.to_dict())

    def delete_job(self, job_id: str) -> bool:
        job = store.get(job_id)
        if not job: return False
        if job.status == JobStatus.RUNNING:
            job.mark_cancelled(); store.save(job)
        if job.output_path:
            file_service.delete_file(job.output_path)
        file_service.delete_upload_dir(job_id)
        return store.delete(job_id)

    def get_stats(self, user_id=None) -> dict:
        counts = store.count_by_status(user_id=user_id)
        all_jobs = store.all(user_id=user_id)
        completed = [j for j in all_jobs if j.status == JobStatus.COMPLETED and j.duration_seconds]
        avg = sum(j.duration_seconds for j in completed) / len(completed) if completed else None
        return {"total_jobs": store.count(user_id=user_id), "by_status": counts,
                "avg_duration_seconds": round(avg, 2) if avg else None}

    async def run_pipeline(self, job_id: str) -> None:
        job = store.get(job_id)
        if not job: return

        def on_progress(progress: int, stage: str) -> None:
            j = store.get(job_id)
            if j and not j.is_terminal:
                j.update_progress(progress, stage); store.save(j)

        job.mark_running("initializing"); store.save(job)

        try:
            output_path = await pipeline.run(job, on_progress)
            from app.core.config import settings
            rel_path = output_path.split(settings.OUTPUT_DIR)[-1].lstrip("/\\")
            output_url = f"/outputs/{rel_path}"
            job = store.get(job_id)
            if job and not job.is_terminal:
                job.mark_completed(output_path, output_url); store.save(job)
                logger.info(f"[{job_id}] Completed in {job.duration_seconds:.1f}s")
        except Exception as exc:
            # Teknik detay sadece logda tutulur; kullanıcıya sade bir mesaj gösterilir.
            logger.error(f"[{job_id}] Failed: {exc}", exc_info=True)
            job = store.get(job_id)
            if job and not job.is_terminal:
                job.mark_failed(to_user_message(exc)); store.save(job)

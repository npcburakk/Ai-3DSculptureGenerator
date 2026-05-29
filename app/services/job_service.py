"""
Job Service
"""

import logging
import uuid
from typing import Optional

from app.core.constants import JobStatus
from app.models.job_model import JobModel
from app.schemas.job_schema import JobCreateRequest, JobResponse, JobListResponse
from app.services.pipeline_service import PipelineService
from app.database.db_store import store

logger = logging.getLogger(__name__)
pipeline = PipelineService()


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

    def delete_job(self, job_id: str) -> bool:
        job = store.get(job_id)
        if not job: return False
        if job.status == JobStatus.RUNNING:
            job.mark_cancelled(); store.save(job)
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
            logger.error(f"[{job_id}] Failed: {exc}", exc_info=True)
            job = store.get(job_id)
            if job and not job.is_terminal:
                job.mark_failed(str(exc)); store.save(job)

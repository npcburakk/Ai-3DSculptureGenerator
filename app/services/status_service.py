from app.schemas.job_schema import JobStatusResponse
from app.database.db_store import store


class StatusService:
    def get_status(self, job_id: str) -> JobStatusResponse | None:
        job = store.get(job_id)
        if not job:
            return None
        return JobStatusResponse(
            id=job.id,
            status=job.status,
            progress=job.progress,
            current_stage=job.current_stage,
            error_message=job.error_message,
            output_url=job.output_url,
        )
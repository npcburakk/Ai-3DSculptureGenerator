"""
API Routes — Text-to-3D Generator
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from typing import Optional

from app.schemas.job_schema import (
    JobCreateRequest, JobResponse, JobListResponse,
    JobStatusResponse, PromptEnhanceRequest, PromptEnhanceResponse,
)
from app.schemas.user_schema import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from app.services.job_service import JobService
from app.services.status_service import StatusService
from app.services.prompt_service import PromptService
from app.auth.user_service import UserService as UserSvc
from app.auth.auth_bearer import get_current_user, require_current_user
from app.core.constants import SupportedBackends, OutputFormat, ImageUpload, JobStatus
from app.core.config import settings
from app.database.db_models import UserDB

router = APIRouter()
job_service = JobService()
status_service = StatusService()
prompt_service = PromptService()
user_service = UserSvc()


@router.post("/auth/register", response_model=UserResponse, status_code=201, tags=["Auth"])
async def register(payload: UserRegisterRequest):
    return user_service.register(payload)

@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login(payload: UserLoginRequest):
    return user_service.login(payload)

@router.get("/auth/me", response_model=UserResponse, tags=["Auth"])
async def get_me(current_user: UserDB = Depends(require_current_user)):
    return user_service.get_profile(current_user)

@router.post("/prompt/enhance", response_model=PromptEnhanceResponse, tags=["Prompt"])
async def enhance_prompt(payload: PromptEnhanceRequest):
    result = await prompt_service.enhance(payload.prompt, payload.style)
    return PromptEnhanceResponse(**result)

@router.post("/jobs", response_model=JobResponse, status_code=202, tags=["Jobs"])
async def create_job(
    payload: JobCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[UserDB] = Depends(get_current_user),
):
    user_id = current_user.id if current_user else None
    # Mock backend is hidden from the UI. It is only reachable via the API
    # (curl/Postman) when explicitly enabled through ENABLE_MOCK_BACKEND.
    if payload.backend == "mock" and not settings.ENABLE_MOCK_BACKEND:
        raise HTTPException(status_code=403, detail="Mock backend is disabled")
    if payload.enhance_prompt and payload.prompt:
        result = await prompt_service.enhance(payload.prompt, payload.style)
        enhanced = result["enhanced"]
    else:
        enhanced = payload.prompt
    job = job_service.create_job(payload, user_id=user_id, enhanced_prompt=enhanced)
    background_tasks.add_task(job_service.run_pipeline, job.id)
    return job

@router.post("/jobs/image", response_model=JobResponse, status_code=202, tags=["Jobs"])
async def create_image_job(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    style: str = Form("realistic"),
    output_format: str = Form("obj"),
    current_user: Optional[UserDB] = Depends(get_current_user),
):
    if not (ImageUpload.MIN_FILES <= len(files) <= ImageUpload.MAX_FILES):
        raise HTTPException(
            status_code=422,
            detail=f"{ImageUpload.MIN_FILES}-{ImageUpload.MAX_FILES} arasında fotoğraf yükleyin",
        )
    if output_format not in OutputFormat.ALL:
        raise HTTPException(status_code=422, detail=f"output_format must be one of: {OutputFormat.ALL}")

    images: list[tuple[bytes, str]] = []
    for f in files:
        if f.content_type not in ImageUpload.ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=422, detail=f"Desteklenmeyen dosya türü: {f.content_type}")
        content = await f.read()
        if len(content) > ImageUpload.MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=422, detail="Her fotoğraf en fazla 10MB olabilir")
        images.append((content, f.filename or "photo.jpg"))

    user_id = current_user.id if current_user else None
    job = job_service.create_image_job(images, style=style, output_format=output_format, user_id=user_id)
    background_tasks.add_task(job_service.run_pipeline, job.id)
    return job

@router.get("/jobs", response_model=JobListResponse, tags=["Jobs"])
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    current_user: Optional[UserDB] = Depends(get_current_user),
):
    user_id = current_user.id if current_user else None
    return job_service.list_jobs(page=page, page_size=page_size, status_filter=status_filter, user_id=user_id)

@router.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
async def get_job(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job

@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse, tags=["Jobs"])
async def get_job_status(job_id: str):
    status = status_service.get_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return status

@router.post("/jobs/{job_id}/retry", response_model=JobResponse, status_code=202, tags=["Jobs"])
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: Optional[UserDB] = Depends(get_current_user),
):
    existing = job_service.get_job(job_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    if existing.status != JobStatus.FAILED:
        raise HTTPException(status_code=409, detail="Only failed jobs can be retried")
    if existing.backend == "mock" and not settings.ENABLE_MOCK_BACKEND:
        raise HTTPException(status_code=403, detail="Mock backend is disabled")
    user_id = current_user.id if current_user else None
    new_job = job_service.retry_job(job_id, user_id=user_id)
    background_tasks.add_task(job_service.run_pipeline, new_job.id)
    return new_job

@router.patch("/jobs/{job_id}/favorite", response_model=JobResponse, tags=["Jobs"])
async def toggle_favorite(job_id: str):
    job = job_service.toggle_favorite(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job

@router.delete("/jobs/{job_id}", status_code=204, tags=["Jobs"])
async def delete_job(job_id: str):
    success = job_service.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

@router.get("/jobs/{job_id}/download", tags=["Jobs"])
async def download_output(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="Job is not completed yet")
    if not job.output_path:
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(
        path=job.output_path,
        media_type="application/octet-stream",
        filename=f"{job_id}.{job.output_format}",
    )

@router.get("/models", tags=["Meta"])
async def list_models():
    # Only expose backends offered in the UI. Mock stays hidden unless it is
    # explicitly enabled for API-only testing.
    backends = [
        b for b in SupportedBackends.ALL
        if b["id"] != "mock" or settings.ENABLE_MOCK_BACKEND
    ]
    return {"backends": backends}

@router.get("/stats", tags=["Meta"])
async def get_stats(current_user: Optional[UserDB] = Depends(get_current_user)):
    user_id = current_user.id if current_user else None
    return job_service.get_stats(user_id=user_id)

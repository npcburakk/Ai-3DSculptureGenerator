"""
API Routes — Text-to-3D Generator
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Depends
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
from app.core.constants import SupportedBackends
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
    if payload.enhance_prompt and payload.prompt:
        result = await prompt_service.enhance(payload.prompt, payload.style)
        enhanced = result["enhanced"]
    else:
        enhanced = payload.prompt
    job = job_service.create_job(payload, user_id=user_id, enhanced_prompt=enhanced)
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
    return {"backends": SupportedBackends.ALL}

@router.get("/stats", tags=["Meta"])
async def get_stats(current_user: Optional[UserDB] = Depends(get_current_user)):
    user_id = current_user.id if current_user else None
    return job_service.get_stats(user_id=user_id)

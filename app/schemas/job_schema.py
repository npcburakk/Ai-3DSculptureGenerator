"""
Pydantic Schemas
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator

from app.core.constants import OutputFormat, SupportedBackends


class PostProcessingOptions(BaseModel):
    enabled: bool = False
    clean: bool = True
    decimate: float = Field(default=1.0, ge=0.1, le=1.0)
    smooth: bool = False
    smooth_iterations: int = Field(default=3, ge=1, le=10)
    target_size_mm: float = Field(default=100.0, ge=10.0, le=500.0)


class JobCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)
    backend: str = Field(default="shap_e")
    output_format: str = Field(default="obj")
    num_steps: int = Field(default=64, ge=16, le=256)
    guidance_scale: float = Field(default=15.0, ge=1.0, le=30.0)
    mesh_resolution: int = Field(default=128, ge=32, le=512)
    style: str = Field(default="realistic")
    enhance_prompt: bool = Field(default=False)
    post_processing: PostProcessingOptions = Field(default_factory=PostProcessingOptions)

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, v: str) -> str:
        if v not in SupportedBackends.IDS:
            raise ValueError(f"backend must be one of: {SupportedBackends.IDS}")
        return v

    @field_validator("output_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        if v not in OutputFormat.ALL:
            raise ValueError(f"output_format must be one of: {OutputFormat.ALL}")
        return v


class JobResponse(BaseModel):
    id: str
    prompt: str
    enhanced_prompt: Optional[str] = None
    style: Optional[str] = None
    backend: str
    output_format: str
    status: str
    progress: int = Field(ge=0, le=100)
    current_stage: Optional[str] = None
    output_path: Optional[str] = None
    output_url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    model_config = {"from_attributes": True}


class JobStatusResponse(BaseModel):
    id: str
    status: str
    progress: int
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    output_url: Optional[str] = None


class JobListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    jobs: list[JobResponse]


class PromptEnhanceRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)
    style: str = Field(default="realistic")


class PromptEnhanceResponse(BaseModel):
    original: str
    enhanced: str
    style: str

"""
Application Configuration
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ────────────────────────────────────
    APP_NAME: str = "Text-to-3D Generator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Server ─────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["*"]

    # ── Database ───────────────────────────────
    DATABASE_URL: str = "sqlite:///./text3d.db"

    # ── Paths ──────────────────────────────────
    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    OUTPUT_DIR: str = "outputs"

    # ── AI Backend ─────────────────────────────
    DEFAULT_BACKEND: str = "shap_e"

    # ── Meshy API ──────────────────────────────
    MESHY_API_KEY: str = ""

    # ── OpenAI API ─────────────────────────────
    OPENAI_API_KEY: str = ""

    # ── Auth ───────────────────────────────────
    SECRET_KEY: str = "change-this-in-production-use-a-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 gün

    # ── Shap-E ─────────────────────────────────
    SHAP_E_GUIDANCE_SCALE: float = 15.0
    SHAP_E_NUM_STEPS: int = 64
    SHAP_E_RENDER_MODE: str = "stf"

    # ── Job Settings ───────────────────────────
    MAX_CONCURRENT_JOBS: int = 2
    JOB_TIMEOUT_SECONDS: int = 600
    MAX_PROMPT_LENGTH: int = 500

    # ── Output ─────────────────────────────────
    DEFAULT_OUTPUT_FORMAT: str = "obj"
    MESH_RESOLUTION: int = 128


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

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
    UPLOAD_DIR: str = "uploads"

    # ── AI Backend ─────────────────────────────
    DEFAULT_BACKEND: str = "meshy"
    # Mock backend is hidden from the UI. When true it can still be exercised
    # directly through the API (curl/Postman) for testing.
    ENABLE_MOCK_BACKEND: bool = False

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


def _apply_user_config(s: Settings) -> None:
    """
    ~/.text3d/config.json içindeki key'ler (Ayarlar ekranından kaydedilir)
    .env'deki değerlerin üzerine yazar — böylece kullanıcı Ayarlar'dan
    girdiği key, .env'de bir şey olmasa bile geçerli olur. Config
    dosyasında olmayan/boş alanlar .env değerini değiştirmez.
    """
    from app.core.user_config import load_user_config

    user_cfg = load_user_config()
    if user_cfg.get("meshy_api_key"):
        s.MESHY_API_KEY = user_cfg["meshy_api_key"]
    if user_cfg.get("openai_api_key"):
        s.OPENAI_API_KEY = user_cfg["openai_api_key"]


def _apply_frozen_paths(s: Settings) -> None:
    """
    PyInstaller ile paketlenmiş (.app) halde çalışırken DB/outputs/uploads
    gibi yazılabilir veriler paketin içine değil, kullanıcının kendi
    Application Support dizinine yazılır — .app salt-okunur olabilir ve
    güncelleme/silmede içeriği kaybolur; geliştirmede davranış değişmez.
    """
    from app.core.paths import is_frozen, get_user_data_dir

    if not is_frozen():
        return
    data_dir = get_user_data_dir()
    (data_dir / "outputs").mkdir(parents=True, exist_ok=True)
    (data_dir / "uploads").mkdir(parents=True, exist_ok=True)
    s.BASE_DIR = data_dir
    s.OUTPUT_DIR = str(data_dir / "outputs")
    s.UPLOAD_DIR = str(data_dir / "uploads")
    s.DATABASE_URL = f"sqlite:///{data_dir / 'text3d.db'}"


settings = get_settings()
_apply_user_config(settings)
_apply_frozen_paths(settings)

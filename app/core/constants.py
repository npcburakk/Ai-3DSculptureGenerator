"""
Application-wide constants
"""


class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    ALL = [PENDING, RUNNING, COMPLETED, FAILED, CANCELLED]
    TERMINAL = [COMPLETED, FAILED, CANCELLED]
    ACTIVE = [PENDING, RUNNING]


class OutputFormat:
    OBJ = "obj"
    PLY = "ply"
    GLB = "glb"
    STL = "stl"
    FBX = "fbx"

    ALL = [OBJ, PLY, GLB, STL, FBX]


class SupportedBackends:
    ALL = [
        {
            "id": "shap_e",
            "name": "Shap-E",
            "description": "OpenAI Shap-E diffusion modeli. Yerel çalışır, GPU gerektirmez.",
            "output_formats": [OutputFormat.OBJ, OutputFormat.PLY, OutputFormat.GLB, OutputFormat.STL],
            "avg_duration_seconds": 300,
            "requires_gpu": False,
        },
        {
            "id": "meshy",
            "name": "Meshy AI",
            "description": "Bulut tabanlı profesyonel 3D üretim. Yüksek kalite.",
            "output_formats": [OutputFormat.OBJ, OutputFormat.GLB, OutputFormat.FBX, OutputFormat.STL],
            "avg_duration_seconds": 120,
            "requires_gpu": False,
        },
        {
            "id": "mock",
            "name": "Mock",
            "description": "Test amaçlı küp mesh üretir. Geliştirme için idealdir.",
            "output_formats": OutputFormat.ALL,
            "avg_duration_seconds": 3,
            "requires_gpu": False,
        },
    ]

    IDS = [b["id"] for b in ALL]


class ImageUpload:
    ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}
    MIN_FILES = 1
    MAX_FILES = 4
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class PipelineStage:
    INITIALIZING = "initializing"
    ENCODING_TEXT = "encoding_text"
    GENERATING_LATENTS = "generating_latents"
    DECODING_MESH = "decoding_mesh"
    EXPORTING_FILE = "exporting_file"
    DONE = "done"

    ORDERED = [
        INITIALIZING,
        ENCODING_TEXT,
        GENERATING_LATENTS,
        DECODING_MESH,
        EXPORTING_FILE,
        DONE,
    ]

    PROGRESS_MAP = {
        INITIALIZING: 5,
        ENCODING_TEXT: 20,
        GENERATING_LATENTS: 60,
        DECODING_MESH: 85,
        EXPORTING_FILE: 95,
        DONE: 100,
    }

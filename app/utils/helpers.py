import re
import uuid
from datetime import datetime


def generate_job_id() -> str:
    return str(uuid.uuid4())


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:64]


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))
import re
from app.core.constants import OutputFormat, SupportedBackends


def validate_prompt(prompt: str) -> tuple[bool, str]:
    if not prompt or not prompt.strip():
        return False, "Prompt cannot be empty"
    if len(prompt.strip()) < 3:
        return False, "Prompt must be at least 3 characters"
    if len(prompt) > 500:
        return False, "Prompt cannot exceed 500 characters"
    return True, ""


def validate_backend(backend: str) -> tuple[bool, str]:
    if backend not in SupportedBackends.IDS:
        return False, f"Backend must be one of: {SupportedBackends.IDS}"
    return True, ""


def validate_output_format(fmt: str) -> tuple[bool, str]:
    if fmt not in OutputFormat.ALL:
        return False, f"Output format must be one of: {OutputFormat.ALL}"
    return True, ""


def is_valid_job_id(job_id: str) -> bool:
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    return bool(uuid_pattern.match(job_id))
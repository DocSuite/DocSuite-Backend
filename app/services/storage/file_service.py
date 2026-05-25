from pathlib import Path
import re
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import DocSuiteException


def sanitize_filename(filename: str) -> str:
    safe_name = Path(filename).name.strip()
    safe_name = re.sub(r"\s+", "_", safe_name)
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", safe_name)
    return safe_name or "upload.bin"


async def save_upload_file(file: UploadFile, allowed_extensions: set[str] | None = None) -> Path:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    source_name = sanitize_filename(file.filename or "upload.bin")
    suffix = Path(source_name).suffix
    if allowed_extensions is not None and suffix.lower() not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise DocSuiteException(f"Formato no soportado. Formatos permitidos: {allowed}")

    target_path = settings.upload_dir / f"{uuid4()}{suffix}"

    content = await file.read()
    if not content:
        raise DocSuiteException("El archivo esta vacio")

    target_path.write_bytes(content)
    return target_path

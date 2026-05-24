from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import DocSuiteException


async def save_upload_file(file: UploadFile) -> Path:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    source_name = file.filename or "upload.bin"
    suffix = Path(source_name).suffix
    target_path = settings.upload_dir / f"{uuid4()}{suffix}"

    content = await file.read()
    if not content:
        raise DocSuiteException("El archivo esta vacio")

    target_path.write_bytes(content)
    return target_path

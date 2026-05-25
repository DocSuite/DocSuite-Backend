from fastapi import APIRouter, Query

from app.api.deps import CurrentUser
from app.core.config import get_settings
from app.services.storage.temp_cleaner import CleanupMode, cleanup_storage

router = APIRouter()


@router.post("/storage/cleanup")
def run_storage_cleanup(
    current_user: CurrentUser,
    mode: CleanupMode = Query(
        default=CleanupMode.week,
        description=(
            "all — elimina todos los archivos; "
            "week — elimina archivos con más de 7 días; "
            "month — elimina archivos con más de 30 días"
        ),
    ),
) -> dict:
    settings = get_settings()
    result = cleanup_storage(
        upload_dir=settings.upload_dir.resolve(),
        temp_dir=settings.temp_dir.resolve(),
        processed_dir=settings.processed_dir.resolve(),
        mode=mode,
    )
    return result.summary()

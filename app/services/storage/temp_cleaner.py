from pathlib import Path
from time import time


def clean_old_files(directory: Path, max_age_seconds: int = 86400) -> int:
    if not directory.exists():
        return 0

    deleted = 0
    now = time()
    for file_path in directory.iterdir():
        if file_path.is_file() and now - file_path.stat().st_mtime > max_age_seconds:
            file_path.unlink()
            deleted += 1
    return deleted

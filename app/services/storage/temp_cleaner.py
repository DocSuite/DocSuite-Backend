from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class CleanupMode(str, Enum):
    all = "all"
    week = "week"
    month = "month"


_MODE_AGE: dict[CleanupMode, float | None] = {
    CleanupMode.all: None,
    CleanupMode.week: 7 * 24 * 3600,
    CleanupMode.month: 30 * 24 * 3600,
}


@dataclass
class CleanupResult:
    mode: CleanupMode
    files_deleted: int = 0
    bytes_freed: int = 0
    by_directory: dict[str, int] = field(default_factory=dict)

    def summary(self) -> dict:
        return {
            "mode": self.mode.value,
            "files_deleted": self.files_deleted,
            "bytes_freed": self.bytes_freed,
            "bytes_freed_mb": round(self.bytes_freed / 1_048_576, 2),
            "by_directory": self.by_directory,
        }


def _clean_directory(directory: Path, max_age: float | None) -> tuple[int, int]:
    if not directory.exists():
        return 0, 0

    deleted = 0
    freed = 0
    now = time.time()

    for fp in directory.iterdir():
        if not fp.is_file():
            continue
        if max_age is None or (now - fp.stat().st_mtime) > max_age:
            size = fp.stat().st_size
            fp.unlink(missing_ok=True)
            deleted += 1
            freed += size

    return deleted, freed


def cleanup_storage(
    upload_dir: Path,
    temp_dir: Path,
    processed_dir: Path,
    mode: CleanupMode = CleanupMode.week,
) -> CleanupResult:
    max_age = _MODE_AGE[mode]
    result = CleanupResult(mode=mode)

    for directory in (upload_dir, temp_dir, processed_dir):
        deleted, freed = _clean_directory(directory, max_age)
        result.files_deleted += deleted
        result.bytes_freed += freed
        result.by_directory[directory.name] = deleted

    return result

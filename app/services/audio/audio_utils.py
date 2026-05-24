from pathlib import Path


AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}


def is_audio_file(file_path: Path) -> bool:
    return file_path.suffix.lower() in AUDIO_EXTENSIONS

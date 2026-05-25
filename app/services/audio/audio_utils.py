from pathlib import Path
import os
import shutil
import subprocess
import wave
from uuid import uuid4

from app.core.config import get_settings


AUDIO_EXTENSIONS = {
    ".aac",
    ".aiff",
    ".amr",
    ".flac",
    ".m4a",
    ".mp3",
    ".mp4",
    ".mpeg",
    ".oga",
    ".ogg",
    ".opus",
    ".wav",
    ".webm",
    ".wma",
}

_FFMPEG_REGISTERED = False


def is_audio_file(file_path: Path) -> bool:
    return file_path.suffix.lower() in AUDIO_EXTENSIONS


def ensure_ffmpeg_available() -> None:
    global _FFMPEG_REGISTERED

    if shutil.which("ffmpeg"):
        return

    try:
        import imageio_ffmpeg
    except ImportError:
        return

    ffmpeg_path = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()

    settings = get_settings()
    alias_dir = settings.storage_bin_dir.resolve()
    alias_dir.mkdir(parents=True, exist_ok=True)

    alias_path = alias_dir / ffmpeg_path.name
    if not alias_path.exists():
        shutil.copy2(ffmpeg_path, alias_path)

    if not _FFMPEG_REGISTERED:
        os.environ["PATH"] = f"{alias_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        _FFMPEG_REGISTERED = True


def load_audio_for_pyannote(file_path: Path) -> dict:
    import numpy as np
    import torch

    ensure_ffmpeg_available()

    settings = get_settings()
    temp_dir = settings.temp_dir.resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    wav_path = temp_dir / f"{uuid4()}.wav"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(file_path.resolve()),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-sample_fmt",
            "s16",
            str(wav_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    with wave.open(str(wav_path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        frames = wav_file.readframes(wav_file.getnframes())

    wav_path.unlink(missing_ok=True)

    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    waveform = torch.from_numpy(audio).unsqueeze(0)
    return {"waveform": waveform, "sample_rate": sample_rate}

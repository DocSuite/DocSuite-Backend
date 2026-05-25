from pathlib import Path

from app.services.audio.audio_utils import ensure_ffmpeg_available
from app.services.audio.model_registry import get_whisper_model


async def transcribe_audio(file_path: Path) -> str:
    return transcribe_audio_sync(file_path)


def transcribe_audio_sync(file_path: Path) -> str:
    ensure_ffmpeg_available()
    model = get_whisper_model()
    result = model.transcribe(str(file_path.resolve()), language="es")
    text = result.get("text", "")
    return text.strip()

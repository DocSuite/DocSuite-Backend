from pathlib import Path

from app.core.config import get_settings
from app.services.audio.audio_utils import ensure_ffmpeg_available, get_wav_duration, split_audio_into_chunks
from app.services.audio.model_registry import get_whisper_model


async def transcribe_audio(file_path: Path) -> str:
    return transcribe_audio_sync(file_path)


def transcribe_audio_sync(file_path: Path) -> str:
    ensure_ffmpeg_available()
    settings = get_settings()
    model = get_whisper_model()
    lang = None if settings.whisper_language == "auto" else settings.whisper_language

    duration = get_wav_duration(file_path)
    if duration is not None and duration > settings.whisper_chunk_threshold:
        return _transcribe_chunked(file_path, model, lang, settings)

    result = model.transcribe(str(file_path.resolve()), language=lang)
    return result.get("text", "").strip()


def _transcribe_chunked(file_path: Path, model, lang: str | None, settings) -> str:
    temp_dir = settings.temp_dir.resolve()
    chunks = split_audio_into_chunks(file_path, settings.whisper_chunk_size, temp_dir)
    texts: list[str] = []
    try:
        for chunk in chunks:
            result = model.transcribe(str(chunk), language=lang)
            text = result.get("text", "").strip()
            if text:
                texts.append(text)
    finally:
        for chunk in chunks:
            chunk.unlink(missing_ok=True)
    return " ".join(texts)

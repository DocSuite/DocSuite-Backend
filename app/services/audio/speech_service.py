from pathlib import Path

from app.core.config import get_settings
from app.services.audio.deepgram_service import transcribe_with_deepgram
from app.services.audio.diarizer import diarize_audio_sync
from app.services.audio.transcriber import transcribe_audio_sync


def use_deepgram() -> bool:
    return get_settings().transcription_provider.lower() == "deepgram"


def transcribe_and_diarize_audio(file_path: Path) -> tuple[str, dict]:
    if use_deepgram():
        return transcribe_with_deepgram(file_path)

    transcription = transcribe_audio_sync(file_path)
    diarization = diarize_audio_sync(file_path)
    return transcription, diarization

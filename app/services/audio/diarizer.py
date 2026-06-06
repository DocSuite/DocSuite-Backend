import logging
from pathlib import Path
from typing import Any

from app.services.audio.audio_utils import ensure_ffmpeg_available, load_audio_for_pyannote
from app.services.audio.model_registry import get_pyannote_pipeline

logger = logging.getLogger(__name__)


async def diarize_audio(file_path: Path) -> dict:
    return diarize_audio_sync(file_path)


def diarize_audio_sync(file_path: Path) -> dict:
    ensure_ffmpeg_available()
    pipeline = get_pyannote_pipeline()
    audio = load_audio_for_pyannote(file_path)
    try:
        diarization = pipeline(audio)
    except (RuntimeError, ValueError) as exc:
        if is_empty_diarization_error(exc):
            logger.warning("Diarizacion omitida por audio sin segmentos utiles: %s", exc)
            return {"segments": []}
        raise
    return build_diarization_payload(diarization)


def is_empty_diarization_error(exc: Exception) -> bool:
    message = str(exc)
    return "cannot reshape tensor of 0 elements" in message or "shape [1, 0, 20, -1]" in message


def build_diarization_payload(diarization: Any) -> dict:
    annotation = getattr(diarization, "speaker_diarization", diarization)
    segments = []
    for turn, _, speaker in annotation.itertracks(yield_label=True):
        segments.append({"speaker": speaker, "start": turn.start, "end": turn.end})
    return {"segments": segments}

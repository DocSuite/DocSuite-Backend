from pathlib import Path

from app.services.audio.audio_utils import ensure_ffmpeg_available, load_audio_for_pyannote
from app.services.audio.model_registry import get_pyannote_pipeline


async def diarize_audio(file_path: Path) -> dict:
    return diarize_audio_sync(file_path)


def diarize_audio_sync(file_path: Path) -> dict:
    ensure_ffmpeg_available()
    pipeline = get_pyannote_pipeline()
    audio = load_audio_for_pyannote(file_path)
    diarization = pipeline(audio)
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({"speaker": speaker, "start": turn.start, "end": turn.end})
    return {"segments": segments}

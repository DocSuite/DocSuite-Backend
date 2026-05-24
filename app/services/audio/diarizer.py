from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import DocSuiteException


async def diarize_audio(file_path: Path) -> dict:
    settings = get_settings()
    if settings.hf_token is None:
        raise DocSuiteException("HF_TOKEN no configurado", status_code=503)

    try:
        from pyannote.audio import Pipeline
    except ImportError as exc:
        raise DocSuiteException("pyannote.audio no esta instalado", status_code=503) from exc

    pipeline = Pipeline.from_pretrained(settings.pyannote_model, token=settings.hf_token)
    diarization = pipeline(str(file_path))
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({"speaker": speaker, "start": turn.start, "end": turn.end})
    return {"segments": segments}

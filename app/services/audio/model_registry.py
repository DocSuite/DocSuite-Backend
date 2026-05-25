import logging
from threading import Lock

logger = logging.getLogger(__name__)

_lock = Lock()
_whisper_model = None
_pyannote_pipeline = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    with _lock:
        if _whisper_model is not None:
            return _whisper_model
        _load_whisper()
    return _whisper_model


def _load_whisper() -> None:
    global _whisper_model
    from app.core.config import get_settings
    from app.core.exceptions import DocSuiteException
    from app.services.audio.audio_utils import ensure_ffmpeg_available

    settings = get_settings()
    ensure_ffmpeg_available()

    try:
        import torch
        import whisper
    except ImportError as exc:
        raise DocSuiteException("Whisper o PyTorch no están instalados", status_code=503) from exc

    device = settings.whisper_device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    logger.info("Cargando Whisper %s en %s...", settings.whisper_model, device)
    _whisper_model = whisper.load_model(settings.whisper_model, device=device)
    logger.info("Whisper listo.")


def get_pyannote_pipeline():
    global _pyannote_pipeline
    if _pyannote_pipeline is not None:
        return _pyannote_pipeline
    with _lock:
        if _pyannote_pipeline is not None:
            return _pyannote_pipeline
        _load_pyannote()
    return _pyannote_pipeline


def _load_pyannote() -> None:
    global _pyannote_pipeline
    from app.core.config import get_settings
    from app.core.exceptions import DocSuiteException
    from app.services.audio.audio_utils import ensure_ffmpeg_available

    settings = get_settings()
    ensure_ffmpeg_available()

    if settings.hf_token is None:
        raise DocSuiteException("HF_TOKEN no configurado", status_code=503)

    try:
        import torch
        from pyannote.audio import Pipeline
    except ImportError as exc:
        raise DocSuiteException("pyannote.audio o PyTorch no están instalados", status_code=503) from exc

    logger.info("Cargando pyannote %s...", settings.pyannote_model)
    pipeline = Pipeline.from_pretrained(settings.pyannote_model, token=settings.hf_token)

    device = settings.pyannote_device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    pipeline.to(torch.device(device))

    _pyannote_pipeline = pipeline
    logger.info("pyannote listo.")


def preload_all_models() -> None:
    try:
        get_whisper_model()
    except Exception as exc:
        logger.warning("No se pudo precargar Whisper: %s", exc)

    try:
        get_pyannote_pipeline()
    except Exception as exc:
        logger.warning("No se pudo precargar pyannote: %s", exc)

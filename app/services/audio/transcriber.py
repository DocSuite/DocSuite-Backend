from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import DocSuiteException


async def transcribe_audio(file_path: Path) -> str:
    settings = get_settings()
    try:
        import whisper
    except ImportError as exc:
        raise DocSuiteException("Whisper no esta instalado", status_code=503) from exc

    model = whisper.load_model(settings.whisper_model, device="cuda")
    result = model.transcribe(str(file_path), language="es")
    text = result.get("text", "")
    return text.strip()

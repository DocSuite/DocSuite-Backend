import json
import mimetypes
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import DocSuiteException


def transcribe_with_deepgram(file_path: Path) -> tuple[str, dict]:
    settings = get_settings()
    if not settings.deepgram_api_key:
        raise DocSuiteException("DEEPGRAM_API_KEY no esta configurado", status_code=503)

    params = {
        "model": settings.deepgram_model,
        "language": settings.deepgram_language,
        "diarize_model": settings.deepgram_diarize_model,
        "punctuate": "true",
        "smart_format": "true",
        "utterances": "true",
    }
    url = f"https://api.deepgram.com/v1/listen?{urllib.parse.urlencode(params)}"
    content_type = mimetypes.guess_type(file_path.name)[0] or "audio/wav"

    request = urllib.request.Request(
        url,
        data=file_path.read_bytes(),
        headers={
            "Authorization": f"Token {settings.deepgram_api_key}",
            "Content-Type": content_type,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=settings.deepgram_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise DocSuiteException(f"Deepgram rechazo el audio: {detail[:300]}", status_code=502) from exc
    except urllib.error.URLError as exc:
        raise DocSuiteException(f"No se pudo conectar con Deepgram: {exc.reason}", status_code=502) from exc

    return parse_deepgram_payload(payload)


def parse_deepgram_payload(payload: dict[str, Any]) -> tuple[str, dict]:
    results = payload.get("results", {})
    channels = results.get("channels", [])
    alternative = channels[0].get("alternatives", [{}])[0] if channels else {}
    utterances = results.get("utterances") or []

    transcription = build_transcription(alternative, utterances)
    diarization = build_diarization(alternative, utterances)
    return transcription, diarization


def build_transcription(alternative: dict[str, Any], utterances: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for utterance in utterances:
        transcript = str(utterance.get("transcript") or "").strip()
        if transcript:
            speaker = format_speaker(utterance.get("speaker"))
            lines.append(f"{speaker}: {transcript}")

    if lines:
        return "\n".join(lines)

    return str(alternative.get("transcript") or "").strip()


def build_diarization(alternative: dict[str, Any], utterances: list[dict[str, Any]]) -> dict:
    segments = []
    for utterance in utterances:
        transcript = str(utterance.get("transcript") or "").strip()
        start = utterance.get("start")
        end = utterance.get("end")
        if transcript and isinstance(start, int | float) and isinstance(end, int | float):
            segments.append(
                {
                    "speaker": format_speaker(utterance.get("speaker")),
                    "start": float(start),
                    "end": float(end),
                    "text": transcript,
                }
            )

    if segments:
        return {"segments": segments}

    return {"segments": build_segments_from_words(alternative.get("words") or [])}


def build_segments_from_words(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_words: list[str] = []

    for word in words:
        speaker = format_speaker(word.get("speaker"))
        text = str(word.get("punctuated_word") or word.get("word") or "").strip()
        start = word.get("start")
        end = word.get("end")
        if not text or not isinstance(start, int | float) or not isinstance(end, int | float):
            continue

        if current is None or current["speaker"] != speaker:
            if current is not None:
                current["text"] = " ".join(current_words)
                segments.append(current)
            current = {"speaker": speaker, "start": float(start), "end": float(end)}
            current_words = [text]
            continue

        current["end"] = float(end)
        current_words.append(text)

    if current is not None:
        current["text"] = " ".join(current_words)
        segments.append(current)

    return segments


def format_speaker(value: Any) -> str:
    if value is None:
        return "SPEAKER_00"
    try:
        return f"SPEAKER_{int(value):02d}"
    except (TypeError, ValueError):
        return str(value)

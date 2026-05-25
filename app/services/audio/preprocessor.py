import logging
import subprocess
from pathlib import Path
from uuid import uuid4

import numpy as np

from app.core.config import get_settings
from app.services.audio.audio_utils import ensure_ffmpeg_available

logger = logging.getLogger(__name__)

_TARGET_RMS = 0.08


def _to_wav_16k(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src.resolve()),
            "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
            str(dst.resolve()),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _rms_normalize(audio: np.ndarray) -> np.ndarray:
    rms = np.sqrt(np.mean(audio ** 2))
    if rms < 1e-6:
        return audio
    gain = _TARGET_RMS / rms
    return np.clip(audio * gain, -1.0, 1.0)


def preprocess_audio(file_path: Path) -> Path:
    ensure_ffmpeg_available()

    settings = get_settings()
    temp_dir = settings.temp_dir.resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)

    uid = uuid4().hex
    wav_raw = temp_dir / f"{uid}_raw.wav"
    wav_out = temp_dir / f"{uid}_prep.wav"

    _to_wav_16k(file_path, wav_raw)

    try:
        import soundfile as sf

        audio, sr = sf.read(str(wav_raw))

        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        audio = audio.astype(np.float32)

        try:
            import noisereduce as nr
            audio = nr.reduce_noise(y=audio, sr=sr, stationary=False).astype(np.float32)
        except Exception as exc:
            logger.warning("Reduccion de ruido omitida: %s", exc)

        audio = _rms_normalize(audio)

        sf.write(str(wav_out), audio, sr, subtype="PCM_16")

    finally:
        wav_raw.unlink(missing_ok=True)

    return wav_out

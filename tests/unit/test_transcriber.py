from pathlib import Path

from app.services.audio.audio_utils import is_audio_file


def test_is_audio_file() -> None:
    assert is_audio_file(Path("meeting.wav")) is True
    assert is_audio_file(Path("document.pdf")) is False

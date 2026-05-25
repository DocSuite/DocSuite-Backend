from pathlib import Path

from app.services.audio.diarizer import build_diarization_payload
from app.services.audio.audio_utils import is_audio_file


def test_is_audio_file() -> None:
    assert is_audio_file(Path("meeting.wav")) is True
    assert is_audio_file(Path("document.pdf")) is False


class FakeTurn:
    start = 1.5
    end = 3.0


class FakeAnnotation:
    def itertracks(self, yield_label: bool = False):
        assert yield_label is True
        yield FakeTurn(), "track", "SPEAKER_00"


class FakeDiarizeOutput:
    speaker_diarization = FakeAnnotation()


def test_build_diarization_payload_supports_diarize_output() -> None:
    result = build_diarization_payload(FakeDiarizeOutput())

    assert result == {
        "segments": [
            {
                "speaker": "SPEAKER_00",
                "start": 1.5,
                "end": 3.0,
            }
        ]
    }

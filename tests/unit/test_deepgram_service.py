from app.services.audio.deepgram_service import parse_deepgram_payload


def test_parse_deepgram_payload_uses_utterances() -> None:
    payload = {
        "results": {
            "channels": [
                {
                    "alternatives": [
                        {
                            "transcript": "hola profesor listo",
                            "words": [],
                        }
                    ]
                }
            ],
            "utterances": [
                {
                    "speaker": 0,
                    "start": 0.2,
                    "end": 1.4,
                    "transcript": "hola profesor",
                },
                {
                    "speaker": 1,
                    "start": 1.5,
                    "end": 2.7,
                    "transcript": "listo",
                },
            ],
        }
    }

    transcription, diarization = parse_deepgram_payload(payload)

    assert transcription == "SPEAKER_00: hola profesor\nSPEAKER_01: listo"
    assert diarization == {
        "segments": [
            {"speaker": "SPEAKER_00", "start": 0.2, "end": 1.4, "text": "hola profesor"},
            {"speaker": "SPEAKER_01", "start": 1.5, "end": 2.7, "text": "listo"},
        ]
    }


def test_parse_deepgram_payload_falls_back_to_words() -> None:
    payload = {
        "results": {
            "channels": [
                {
                    "alternatives": [
                        {
                            "transcript": "hola profesor listo",
                            "words": [
                                {"speaker": 0, "start": 0.2, "end": 0.5, "word": "hola"},
                                {"speaker": 0, "start": 0.6, "end": 1.0, "word": "profesor"},
                                {"speaker": 1, "start": 1.5, "end": 2.0, "word": "listo"},
                            ],
                        }
                    ]
                }
            ],
        }
    }

    transcription, diarization = parse_deepgram_payload(payload)

    assert transcription == "hola profesor listo"
    assert diarization == {
        "segments": [
            {"speaker": "SPEAKER_00", "start": 0.2, "end": 1.0, "text": "hola profesor"},
            {"speaker": "SPEAKER_01", "start": 1.5, "end": 2.0, "text": "listo"},
        ]
    }

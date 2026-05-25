from app.services.storage.file_service import sanitize_filename


def test_sanitize_filename_accepts_spaces_and_special_chars() -> None:
    assert sanitize_filename(" Reunion Final 01 (UPAO).mp3 ") == "Reunion_Final_01__UPAO_.mp3"


def test_sanitize_filename_removes_path_parts() -> None:
    assert sanitize_filename("../audio clase.wav") == "audio_clase.wav"

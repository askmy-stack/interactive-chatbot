from __future__ import annotations

from backend.voice.stt import SttEngine


def test_browser_transcript_validation():
    engine = SttEngine()
    result = engine.validate_browser_transcript("  schedule my day  ")
    assert result.text == "schedule my day"
    assert result.backend == "browser_transcript"


def test_available_backends_includes_browser():
    engine = SttEngine()
    assert "browser_transcript" in engine.available_backends


def test_transcribe_file_unavailable(tmp_path):
    engine = SttEngine()
    audio = tmp_path / "empty.wav"
    audio.write_bytes(b"RIFF")
    result = engine.transcribe_file(audio)
    assert result.backend == "unavailable"
    assert result.text == ""

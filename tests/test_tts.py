"""Tests for cross-platform TTS provider abstraction."""

from unittest.mock import patch

from backend.voice.tts import EspeakProvider, MacSayProvider, TtsEngine


def test_tts_engine_status():
    engine = TtsEngine()
    status = engine.status()
    assert "tts_available" in status
    assert "providers" in status


def test_tts_empty_text():
    engine = TtsEngine()
    result = engine.synthesize("")
    assert not result.available
    assert result.unavailable_reason == "empty text"


def test_mac_say_provider_unavailable():
    provider = MacSayProvider()
    with patch("backend.voice.tts.shutil.which", return_value=None):
        assert not provider.is_available()
        result = provider.synthesize("hello")
        assert not result.available


def test_espeak_provider_synthesize():
    provider = EspeakProvider()
    with patch("backend.voice.tts.shutil.which", return_value="/usr/bin/espeak"):
        with patch("backend.voice.tts.run") as mock_run:
            mock_run.return_value.returncode = 0

            def fake_run(cmd, **kwargs):
                out_path = cmd[cmd.index("-w") + 1]
                with open(out_path, "wb") as f:
                    f.write(b"RIFFfake")
                from subprocess import CompletedProcess

                return CompletedProcess(cmd, 0)

            mock_run.side_effect = fake_run
            result = provider.synthesize("hello")
            assert result.available
            assert result.provider == "espeak"


def test_voice_service_tts_status():
    from backend.voice.service import VoiceService

    svc = VoiceService()
    status = svc.tts_status()
    assert "tts_available" in status

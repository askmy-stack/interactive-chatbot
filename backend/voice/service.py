from __future__ import annotations

from backend.voice.stt import SttEngine, SttResult
from backend.voice.tts import TtsEngine, TtsResult


class VoiceService:
    """Local-first voice helpers with cross-platform TTS fallback."""

    def __init__(self) -> None:
        self.stt = SttEngine()
        self.tts = TtsEngine()

    def transcribe_text(self, transcript: str) -> str:
        return self.stt.validate_browser_transcript(transcript).text

    def transcribe_audio(self, audio_bytes: bytes, *, mime_type: str = "audio/wav") -> SttResult:
        return self.stt.transcribe_audio_bytes(audio_bytes, mime_type=mime_type)

    def stt_status(self) -> dict:
        return {
            "backends": self.stt.available_backends,
            "local_stt_available": len(self.stt.available_backends) > 1,
        }

    def tts_status(self) -> dict:
        return self.tts.status()

    def synthesize(self, text: str) -> TtsResult:
        return self.tts.synthesize(text)

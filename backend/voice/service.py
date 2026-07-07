from __future__ import annotations

import base64
import shutil
import tempfile
from pathlib import Path
from subprocess import run

from backend.voice.stt import SttEngine, SttResult


class VoiceService:
    """Local-first voice helpers for macOS.

    STT supports faster-whisper, whisper CLI, or browser transcript validation.
    TTS uses macOS `say` when available.
    """

    def __init__(self) -> None:
        self.stt = SttEngine()

    def transcribe_text(self, transcript: str) -> str:
        return self.stt.validate_browser_transcript(transcript).text

    def transcribe_audio(self, audio_bytes: bytes, *, mime_type: str = "audio/wav") -> SttResult:
        return self.stt.transcribe_audio_bytes(audio_bytes, mime_type=mime_type)

    def stt_status(self) -> dict:
        return {
            "backends": self.stt.available_backends,
            "local_stt_available": len(self.stt.available_backends) > 1,
        }

    def synthesize(self, text: str) -> str:
        if not shutil.which("say"):
            return ""

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ask.aiff"
            proc = run(["say", "-o", str(out), text], capture_output=True, text=True, check=False)
            if proc.returncode != 0 or not out.exists():
                return ""
            return base64.b64encode(out.read_bytes()).decode("utf-8")

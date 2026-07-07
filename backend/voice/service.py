from __future__ import annotations

import base64
import shutil
import tempfile
from pathlib import Path
from subprocess import run


class VoiceService:
    """Local-first voice helpers for macOS.

    The STT path is intentionally simple in v1: callers can send text transcript directly.
    The TTS path uses macOS `say` to generate spoken audio when available.
    """

    def transcribe_text(self, transcript: str) -> str:
        return transcript.strip()

    def synthesize(self, text: str) -> str:
        if not shutil.which("say"):
            return ""

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "jarvis.aiff"
            proc = run(["say", "-o", str(out), text], capture_output=True, text=True, check=False)
            if proc.returncode != 0 or not out.exists():
                return ""
            return base64.b64encode(out.read_bytes()).decode("utf-8")

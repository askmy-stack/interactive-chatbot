"""Speech-to-text backends with graceful local/CI fallbacks."""

from __future__ import annotations

import base64
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from subprocess import run


@dataclass
class SttResult:
    text: str
    backend: str
    confidence: float | None = None


class SttEngine:
    """Local-first STT with optional faster-whisper and browser-transcript fallback."""

    def __init__(self) -> None:
        self._whisper_cli = shutil.which("whisper") or shutil.which("faster-whisper")

    @property
    def available_backends(self) -> list[str]:
        backends = ["browser_transcript"]
        if shutil.which("whisper"):
            backends.append("whisper_cpp")
        try:
            import faster_whisper  # noqa: F401

            backends.append("faster_whisper")
        except ImportError:
            pass
        return backends

    def transcribe_audio_bytes(self, audio_bytes: bytes, *, mime_type: str = "audio/wav") -> SttResult:
        suffix = ".wav" if "wav" in mime_type else ".webm"
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / f"input{suffix}"
            audio_path.write_bytes(audio_bytes)
            return self.transcribe_file(audio_path)

    def transcribe_file(self, audio_path: Path) -> SttResult:
        faster = self._try_faster_whisper(audio_path)
        if faster:
            return faster
        whisper_result = self._try_whisper_cli(audio_path)
        if whisper_result:
            return whisper_result
        return SttResult(text="", backend="unavailable", confidence=None)

    def validate_browser_transcript(self, transcript: str) -> SttResult:
        cleaned = transcript.strip()
        if not cleaned:
            return SttResult(text="", backend="browser_transcript")
        return SttResult(text=cleaned, backend="browser_transcript", confidence=1.0)

    def _try_faster_whisper(self, audio_path: Path) -> SttResult | None:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return None

        try:
            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, _info = model.transcribe(str(audio_path))
            text = " ".join(seg.text.strip() for seg in segments).strip()
            if text:
                return SttResult(text=text, backend="faster_whisper", confidence=0.85)
        except Exception:
            return None
        return None

    def _try_whisper_cli(self, audio_path: Path) -> SttResult | None:
        whisper = shutil.which("whisper")
        if not whisper:
            return None

        with tempfile.TemporaryDirectory() as tmp:
            proc = run(
                [whisper, str(audio_path), "--model", "tiny", "--output_dir", tmp, "--output_format", "txt"],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                return None
            txt_files = list(Path(tmp).glob("*.txt"))
            if not txt_files:
                return None
            text = txt_files[0].read_text(encoding="utf-8").strip()
            if text:
                return SttResult(text=text, backend="whisper_cpp", confidence=0.8)
        return None


def decode_audio_payload(audio_base64: str) -> bytes:
    return base64.b64decode(audio_base64)

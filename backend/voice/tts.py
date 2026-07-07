"""Cross-platform TTS provider abstraction."""

from __future__ import annotations

import base64
import shutil
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from subprocess import run


@dataclass
class TtsResult:
    audio_base64: str
    provider: str
    available: bool
    unavailable_reason: str | None = None


class TtsProvider(ABC):
    name: str

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def synthesize(self, text: str) -> TtsResult:
        pass


class MacSayProvider(TtsProvider):
    name = "macos-say"

    def is_available(self) -> bool:
        return shutil.which("say") is not None

    def synthesize(self, text: str) -> TtsResult:
        if not self.is_available():
            return TtsResult("", self.name, False, "macOS say not found")

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ask.aiff"
            proc = run(["say", "-o", str(out), text], capture_output=True, text=True, check=False)
            if proc.returncode != 0 or not out.exists():
                return TtsResult("", self.name, False, proc.stderr or "say failed")
            return TtsResult(
                base64.b64encode(out.read_bytes()).decode("utf-8"),
                self.name,
                True,
            )


class EspeakProvider(TtsProvider):
    name = "espeak"

    def is_available(self) -> bool:
        return shutil.which("espeak") is not None

    def synthesize(self, text: str) -> TtsResult:
        if not self.is_available():
            return TtsResult("", self.name, False, "espeak not found")

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ask.wav"
            proc = run(
                ["espeak", "-w", str(out), text],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0 or not out.exists():
                return TtsResult("", self.name, False, proc.stderr or "espeak failed")
            return TtsResult(
                base64.b64encode(out.read_bytes()).decode("utf-8"),
                self.name,
                True,
            )


class Pyttsx3Provider(TtsProvider):
    name = "pyttsx3"

    def is_available(self) -> bool:
        try:
            import pyttsx3  # noqa: F401

            return True
        except ImportError:
            return False

    def synthesize(self, text: str) -> TtsResult:
        if not self.is_available():
            return TtsResult("", self.name, False, "pyttsx3 not installed")

        try:
            import pyttsx3

            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "ask.wav"
                engine = pyttsx3.init()
                engine.save_to_file(text, str(out))
                engine.runAndWait()
                if not out.exists():
                    return TtsResult("", self.name, False, "pyttsx3 produced no output")
                return TtsResult(
                    base64.b64encode(out.read_bytes()).decode("utf-8"),
                    self.name,
                    True,
                )
        except Exception as exc:
            return TtsResult("", self.name, False, str(exc))


class TtsEngine:
    """Try providers in order: macOS say → espeak → pyttsx3."""

    def __init__(self) -> None:
        self._providers: list[TtsProvider] = [
            MacSayProvider(),
            EspeakProvider(),
            Pyttsx3Provider(),
        ]

    @property
    def available_providers(self) -> list[str]:
        return [p.name for p in self._providers if p.is_available()]

    def status(self) -> dict:
        providers = self.available_providers
        return {
            "tts_available": bool(providers),
            "providers": providers,
            "active_provider": providers[0] if providers else None,
        }

    def synthesize(self, text: str) -> TtsResult:
        if not text.strip():
            return TtsResult("", "none", False, "empty text")

        last_reason = "No TTS backend available"
        for provider in self._providers:
            if not provider.is_available():
                continue
            result = provider.synthesize(text)
            if result.available and result.audio_base64:
                return result
            last_reason = result.unavailable_reason or f"{provider.name} failed"

        return TtsResult("", "none", False, last_reason)

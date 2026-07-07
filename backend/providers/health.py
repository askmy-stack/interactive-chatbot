"""Provider health probes with ordered fallback recommendations."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from backend.config import settings
from backend.providers.factory import resolve_provider


@dataclass
class ProviderHealth:
    name: str
    healthy: bool
    detail: str


def probe_ollama(timeout: float = 2.0) -> ProviderHealth:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    try:
        resp = httpx.get(url, timeout=timeout)
        if resp.status_code == 200:
            return ProviderHealth("ollama", True, "reachable")
        return ProviderHealth("ollama", False, f"status {resp.status_code}")
    except Exception as exc:
        return ProviderHealth("ollama", False, str(exc))


def probe_openai(timeout: float = 2.0) -> ProviderHealth:
    if not settings.openai_api_key.strip():
        return ProviderHealth("openai", False, "no API key configured")
    try:
        resp = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            timeout=timeout,
        )
        healthy = resp.status_code in (200, 401)
        return ProviderHealth("openai", healthy, f"status {resp.status_code}")
    except Exception as exc:
        return ProviderHealth("openai", False, str(exc))


def probe_openrouter(timeout: float = 2.0) -> ProviderHealth:
    if not settings.openrouter_api_key.strip():
        return ProviderHealth("openrouter", False, "no API key configured")
    try:
        resp = httpx.get(
            f"{settings.openrouter_base_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
            timeout=timeout,
        )
        healthy = resp.status_code in (200, 401)
        return ProviderHealth("openrouter", healthy, f"status {resp.status_code}")
    except Exception as exc:
        return ProviderHealth("openrouter", False, str(exc))


def check_all_providers() -> dict:
    probes = [probe_ollama(), probe_openai(), probe_openrouter()]
    active = resolve_provider()
    fallback_order = ["ollama", "openrouter", "openai"]
    recommended = next((p.name for p in probes if p.healthy), "ollama")
    if active not in {p.name for p in probes if p.healthy}:
        for name in fallback_order:
            match = next((p for p in probes if p.name == name and p.healthy), None)
            if match:
                recommended = match.name
                break

    return {
        "active_provider": active,
        "recommended_fallback": recommended,
        "providers": {p.name: {"healthy": p.healthy, "detail": p.detail} for p in probes},
    }

"""
Shared pytest fixtures.

Uses Ollama as the default provider in tests so no paid API keys are required.
"""

import pytest


@pytest.fixture(autouse=True)
def test_llm_env(monkeypatch):
    """Prefer local Ollama defaults and clear paid keys unless a test overrides them."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "ollama")

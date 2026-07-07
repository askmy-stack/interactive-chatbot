"""
Provider factory tests — no real API calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.providers.factory import effective_model_name, resolve_provider


def test_resolve_provider_defaults_to_ollama_without_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "auto")

    from backend.config import Settings

    with patch("backend.providers.factory.settings", Settings()):
        assert resolve_provider() == "ollama"


def test_resolve_provider_auto_prefers_openai_when_key_set(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_PROVIDER", "auto")

    from backend.config import Settings

    with patch("backend.providers.factory.settings", Settings()):
        assert resolve_provider() == "openai"


def test_resolve_provider_honors_explicit_ollama_over_openai_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")

    from backend.config import Settings

    with patch("backend.providers.factory.settings", Settings()):
        assert resolve_provider() == "ollama"


def test_effective_model_name_uses_provider_default(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.delenv("MODEL_NAME", raising=False)

    from backend.config import Settings

    with patch("backend.providers.factory.settings", Settings()):
        assert effective_model_name("ollama") == "llama3.2"


def test_effective_model_name_honors_override(monkeypatch):
    monkeypatch.setenv("MODEL_NAME", "custom-model")

    from backend.config import Settings

    with patch("backend.providers.factory.settings", Settings()):
        assert effective_model_name("ollama") == "custom-model"


def test_get_chat_model_builds_ollama_client(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")

    from backend.config import Settings
    from backend.providers.factory import get_chat_model

    fake_chat = MagicMock(name="ChatOllama")
    with (
        patch("backend.providers.factory.settings", Settings()),
        patch("langchain_ollama.ChatOllama", fake_chat) as chat_ctor,
    ):
        model = get_chat_model(streaming=True)

    chat_ctor.assert_called_once()
    assert model is chat_ctor.return_value


def test_get_embeddings_uses_ollama_without_openai_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from backend.config import Settings
    from backend.providers.factory import get_embeddings

    fake_embeddings = MagicMock(name="OllamaEmbeddings")
    with (
        patch("backend.providers.factory.settings", Settings()),
        patch("langchain_ollama.OllamaEmbeddings", fake_embeddings) as embed_ctor,
    ):
        embeddings = get_embeddings()

    embed_ctor.assert_called_once()
    assert embeddings is embed_ctor.return_value


def test_get_embeddings_uses_openai_when_provider_is_openai(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    from backend.config import Settings
    from backend.providers.factory import get_embeddings

    fake_embeddings = MagicMock(name="OpenAIEmbeddings")
    with (
        patch("backend.providers.factory.settings", Settings()),
        patch("langchain_openai.OpenAIEmbeddings", fake_embeddings) as embed_ctor,
    ):
        embeddings = get_embeddings()

    embed_ctor.assert_called_once()
    assert embeddings is embed_ctor.return_value


def test_unsupported_provider_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unknown-vendor")

    from backend.config import Settings

    with (
        patch("backend.providers.factory.settings", Settings()),
        pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"),
    ):
        resolve_provider()

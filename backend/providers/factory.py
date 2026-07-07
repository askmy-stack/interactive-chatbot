"""
Provider factory for chat models and embeddings.

Select a backend via LLM_PROVIDER (auto | ollama | openai | openrouter).
When set to auto (default), Ollama is used unless a paid API key is present.
"""

from __future__ import annotations

import structlog
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import SecretStr

from backend.config import settings

log = structlog.get_logger()

SUPPORTED_PROVIDERS = frozenset({"auto", "ollama", "openai", "openrouter"})


def resolve_provider() -> str:
    """Return the active provider name (never 'auto')."""
    requested = settings.llm_provider.strip().lower()
    if requested and requested != "auto":
        if requested not in SUPPORTED_PROVIDERS - {"auto"}:
            raise ValueError(
                f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. "
                f"Use one of: {', '.join(sorted(SUPPORTED_PROVIDERS))}."
            )
        return requested

    if settings.openai_api_key.strip():
        return "openai"
    if settings.openrouter_api_key.strip():
        return "openrouter"
    return "ollama"


def effective_model_name(provider: str | None = None) -> str:
    """Return the model id for the active provider."""
    if settings.model_name.strip():
        return settings.model_name.strip()

    provider = provider or resolve_provider()
    defaults = {
        "ollama": settings.ollama_model,
        "openai": settings.openai_model,
        "openrouter": settings.openrouter_model,
    }
    return defaults[provider]


def get_chat_model(*, streaming: bool = True) -> BaseChatModel:
    """Build a LangChain chat model for the configured provider."""
    provider = resolve_provider()
    model = effective_model_name(provider)

    log.info("llm_provider_selected", provider=provider, model=model)

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model,
            base_url=settings.ollama_base_url,
            temperature=settings.temperature,
        )

    if provider == "openrouter":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            temperature=settings.temperature,
            streaming=streaming,
            api_key=SecretStr(settings.openrouter_api_key),
            base_url=settings.openrouter_base_url,
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model,
        temperature=settings.temperature,
        streaming=streaming,
        api_key=SecretStr(settings.openai_api_key),
    )


def get_embeddings() -> Embeddings:
    """Build embeddings for vector memory using the best available local/paid backend."""
    provider = resolve_provider()

    if provider == "openai" and settings.openai_api_key.strip():
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=settings.openai_embedding_model)

    from langchain_ollama import OllamaEmbeddings

    return OllamaEmbeddings(
        model=settings.ollama_embedding_model,
        base_url=settings.ollama_base_url,
    )

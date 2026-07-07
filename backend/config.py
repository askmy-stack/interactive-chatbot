
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Provider selection: auto | ollama | openai | openrouter
    # auto picks openai when OPENAI_API_KEY is set, else openrouter when configured, else ollama.
    llm_provider: str = "auto"

    # Optional API keys — none are required for local Ollama usage
    openai_api_key: str = ""
    openrouter_api_key: str = ""

    # Model override for the active provider (leave blank to use provider defaults)
    model_name: str = ""
    temperature: float = 0.5

    # Ollama (default free/local path)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_embedding_model: str = "nomic-embed-text"

    # OpenAI defaults (used when OPENAI_API_KEY is set or LLM_PROVIDER=openai)
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # OpenRouter defaults (used when OPENROUTER_API_KEY is set or LLM_PROVIDER=openrouter)
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "meta-llama/llama-3.2-3b-instruct:free"

    # LangSmith observability (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str = "ask-kernel"

    # Memory
    memory_collection: str = "ask_memory"

    # Home Assistant smart home (optional)
    home_assistant_url: str | None = None
    home_assistant_token: str | None = None

    # Backend URL (consumed by Streamlit)
    backend_url: str = "http://localhost:8000"

    # Privacy and operations
    privacy_mode: str = "local_only"  # local_only | hybrid
    redact_pii: bool = True
    backup_dir: str = "./backups"


settings = Settings()

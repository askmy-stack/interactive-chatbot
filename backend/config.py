from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Required
    openai_api_key: str

    # Model
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.5

    # LangSmith observability (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: Optional[str] = None
    langchain_project: str = "jarvis-chatbot"

    # Home Assistant smart home (optional)
    home_assistant_url: Optional[str] = None
    home_assistant_token: Optional[str] = None

    # Backend URL (consumed by Streamlit)
    backend_url: str = "http://localhost:8000"


# Single shared instance — raises ValidationError at startup if OPENAI_API_KEY is missing
settings = Settings()

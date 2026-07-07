# CLAUDE.md

Guidance for AI assistants working in this codebase.

---

## Repository Overview

**A.S.K. (Autonomous System Kernel)** is a personal AI assistant built with LangChain v0.3, FastAPI, and Streamlit.

Core capabilities:
- **Tool-calling agent** — routes user requests to real tools (web search, weather, system info, smart home)
- **Pluggable LLM providers** — Ollama by default (free/local), optional OpenAI and OpenRouter
- **Streaming responses** — tokens stream from the LLM to the browser in real time
- **Persistent vector memory** — ChromaDB stores conversation history across sessions
- **Observability** — structured logging via structlog, optional LangSmith tracing

The assistant persona in prompts is still **Jarvis** — that is intentional and separate from product branding.

---

## File Structure

```
Autonomous-System-Kernel/
├── app.py                        # Streamlit frontend — calls FastAPI backend
├── backend/
│   ├── config.py                 # Pydantic settings (reads .env)
│   ├── providers/                # LLM + embedding factory (Ollama/OpenAI/OpenRouter)
│   ├── memory.py                 # ChromaDB vector memory helpers
│   ├── agent.py                  # LangChain AgentExecutor + astream_response()
│   ├── main.py                   # FastAPI app with /chat/stream, /health, etc.
│   └── tools/
│       ├── system_info.py        # psutil CPU/memory/disk tool
│       ├── web_search.py         # DuckDuckGo search tool
│       ├── weather.py            # Open-Meteo weather tool
│       └── device_control.py    # Home Assistant REST API tool
├── tests/
│   ├── conftest.py               # Sets LLM_PROVIDER=ollama for all tests
│   ├── test_providers.py         # Provider factory tests (mocked)
│   ├── test_tools.py             # Unit tests for tools (no LLM calls)
│   └── test_api.py               # FastAPI endpoint tests (agent mocked)
├── .github/workflows/ci.yml      # GitHub Actions: lint + typecheck + test + secret scan
├── pyproject.toml                # All dependencies + tool config (ruff, mypy, pytest)
├── .env.example                  # Template for env vars (no required API keys)
├── Dockerfile                    # Single-container build (backend + UI)
└── docker-compose.yml            # One-command local deployment
```

---

## Tech Stack

| Component | Package | Default |
|---|---|---|
| LLM | `langchain-ollama` → `ChatOllama` | `llama3.2` via Ollama |
| LLM (optional) | `langchain-openai` → `ChatOpenAI` | `gpt-4o-mini` when key set |
| Agent | `langchain` → `create_tool_calling_agent` + `AgentExecutor` | v0.3 |
| Streaming | `AgentExecutor.astream_events(version="v2")` | — |
| Vector DB | `langchain-chroma` → `Chroma` | Ollama `nomic-embed-text` or OpenAI embeddings |
| Backend | `fastapi` + `uvicorn` | async, StreamingResponse |
| Frontend | `streamlit` | `st.chat_input`, `st.chat_message` |
| Config | `pydantic-settings` → `BaseSettings` | reads `.env` |
| Logging | `structlog` | JSON structured logs |

---

## Running Locally

```bash
# Install deps
pip install uv && uv pip install --system ".[dev]"

# Configure (Ollama default — no paid key required)
cp .env.example .env
ollama pull llama3.2
ollama pull nomic-embed-text

# Start backend (port 8000)
uvicorn backend.main:app --reload

# Start UI (port 8501)
streamlit run app.py
```

Or with Docker:
```bash
docker compose up --build
```

---

## Key Conventions

### Config
- All settings live in `backend/config.py` as a `Settings(BaseSettings)` class
- Single shared `settings` instance imported as `from backend.config import settings`
- No API keys are required — Ollama is the default free/local path
- Tools read `settings` at **call time** (not import time) for testability

### Providers
- `backend/providers/factory.py` resolves `LLM_PROVIDER` (`auto` | `ollama` | `openai` | `openrouter`)
- `auto` prefers OpenAI when `OPENAI_API_KEY` is set, else OpenRouter when configured, else Ollama
- `get_chat_model()` and `get_embeddings()` are the only entry points for model construction

### Agent & Streaming
- The agent singleton is built lazily in `backend/agent.py` via `get_executor()`
- Streaming is done via `astream_events(version="v2")` — yields `on_chat_model_stream` and `on_tool_start` events
- `astream_response()` is an async generator yielding string chunks — it also saves the exchange to ChromaDB after completion
- Never call `get_executor()` at module level in tests without mocking or a running Ollama instance

### Tools
- Each tool is a `@tool`-decorated function in its own file under `backend/tools/`
- All tools must have a clear docstring — LangChain uses it to decide when to call the tool
- `control_device` uses **strict allow-lists** for both domain and action — never pass raw LLM output to external APIs
- Tools that require optional credentials (Home Assistant) return a friendly config message when unconfigured

### FastAPI
- `POST /chat/stream` is the only stateful endpoint — it reads/writes `session_histories`
- `session_histories` is an in-memory dict — acceptable for local use, replace with Redis for multi-instance deployments
- The streaming response media type is `text/plain` — Streamlit reads it with `requests` + `stream=True`

### Streamlit
- `st.session_state.session_id` is a UUID generated once per browser session
- `st.session_state.messages` is a list of `{role, content}` dicts rendered with `st.chat_message`
- The sidebar "example prompts" buttons use `st.session_state.prefill` to pass a value into the next `st.chat_input` render cycle

---

## Testing

```bash
pytest tests/ -v           # all tests
pytest tests/test_tools.py # tools only (no LLM, fast)
pytest tests/test_api.py   # endpoint tests (agent mocked)
pytest tests/test_providers.py  # provider factory (mocked)
```

- `conftest.py` sets `LLM_PROVIDER=ollama` and clears paid API keys for all tests
- API tests mock `astream_response` — no real LLM calls
- Provider tests mock LangChain client constructors — no real API calls
- Tool tests cover: allow-list enforcement, graceful degradation without credentials, real system calls

---

## Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `LLM_PROVIDER` | No | `auto` | Provider selection |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama API URL |
| `OLLAMA_MODEL` | No | `llama3.2` | Default local chat model |
| `OPENAI_API_KEY` | No | — | OpenAI authentication (optional) |
| `OPENROUTER_API_KEY` | No | — | OpenRouter authentication (optional) |
| `MODEL_NAME` | No | provider default | Override model id |
| `TEMPERATURE` | No | `0.5` | LLM temperature |
| `LANGCHAIN_TRACING_V2` | No | `false` | Enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | No | — | LangSmith API key |
| `LANGCHAIN_PROJECT` | No | `ask-kernel` | LangSmith project name |
| `HOME_ASSISTANT_URL` | No | — | Home Assistant base URL |
| `HOME_ASSISTANT_TOKEN` | No | — | HA long-lived access token |
| `BACKEND_URL` | No | `http://localhost:8000` | Backend URL for Streamlit |

**Never commit `.env` to git.** The `.gitignore` excludes it. CI uses `LLM_PROVIDER=ollama`.

---

## Known Issues / Future Work

- Native push-to-talk streaming STT
- Calendar write operations with approval guardrails
- Redis-backed session store for horizontal scaling

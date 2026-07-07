# CLAUDE.md

Guidance for AI assistants working in this codebase.

---

## Repository Overview

**Jarvis** is a personal AI assistant built with LangChain v0.3, FastAPI, and Streamlit.

Core capabilities:
- **Tool-calling agent** — routes user requests to real tools (web search, weather, system info, smart home)
- **Streaming responses** — tokens stream from the LLM to the browser in real time
- **Persistent vector memory** — ChromaDB stores conversation history across sessions
- **Observability** — structured logging via structlog, optional LangSmith tracing

---

## File Structure

```
Interactive-Chatbot/
├── app.py                        # Streamlit frontend — calls FastAPI backend
├── backend/
│   ├── config.py                 # Pydantic settings (reads .env)
│   ├── memory.py                 # ChromaDB vector memory helpers
│   ├── agent.py                  # LangChain AgentExecutor + astream_response()
│   ├── main.py                   # FastAPI app with /chat/stream, /health, etc.
│   └── tools/
│       ├── system_info.py        # psutil CPU/memory/disk tool
│       ├── web_search.py         # DuckDuckGo search tool
│       ├── weather.py            # Open-Meteo weather tool
│       └── device_control.py    # Home Assistant REST API tool
├── tests/
│   ├── conftest.py               # Injects fake OPENAI_API_KEY for all tests
│   ├── test_tools.py             # Unit tests for tools (no LLM calls)
│   └── test_api.py               # FastAPI endpoint tests (agent mocked)
├── .github/workflows/ci.yml      # GitHub Actions: lint + typecheck + test + secret scan
├── langchain.ipynb               # Exploratory LangChain notebook (reference only)
├── pyproject.toml                # All dependencies + tool config (ruff, mypy, pytest)
├── .env.example                  # Template for required env vars
├── Dockerfile                    # Single-container build (backend + UI)
└── docker-compose.yml            # One-command local deployment
```

---

## Tech Stack

| Component | Package | Version |
|---|---|---|
| LLM | `langchain-openai` → `ChatOpenAI` | `gpt-4o-mini` |
| Agent | `langchain` → `create_tool_calling_agent` + `AgentExecutor` | v0.3 |
| Streaming | `AgentExecutor.astream_events(version="v2")` | — |
| Vector DB | `langchain-chroma` → `Chroma` | `text-embedding-3-small` |
| Backend | `fastapi` + `uvicorn` | async, StreamingResponse |
| Frontend | `streamlit` | `st.chat_input`, `st.chat_message` |
| Config | `pydantic-settings` → `BaseSettings` | reads `.env` |
| Logging | `structlog` | JSON structured logs |

---

## Running Locally

```bash
# Install deps
pip install uv && uv pip install --system ".[dev]"

# Configure
cp .env.example .env        # then add OPENAI_API_KEY

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
- `settings` raises `ValidationError` at startup if `OPENAI_API_KEY` is missing — fail fast
- Tools read `settings` at **call time** (not import time) for testability

### Agent & Streaming
- The agent singleton is built lazily in `backend/agent.py` via `get_executor()`
- Streaming is done via `astream_events(version="v2")` — yields `on_chat_model_stream` and `on_tool_start` events
- `astream_response()` is an async generator yielding string chunks — it also saves the exchange to ChromaDB after completion
- Never call `get_executor()` at module level — it requires `OPENAI_API_KEY` to be set

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
```

- `conftest.py` injects `OPENAI_API_KEY=sk-test-placeholder-for-ci` for all tests
- API tests mock `astream_response` — no real OpenAI calls
- Tool tests cover: allow-list enforcement, graceful degradation without credentials, real system calls

---

## Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI API authentication |
| `MODEL_NAME` | No | `gpt-4o-mini` | LLM model ID |
| `TEMPERATURE` | No | `0.5` | LLM temperature |
| `LANGCHAIN_TRACING_V2` | No | `false` | Enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | No | — | LangSmith API key |
| `LANGCHAIN_PROJECT` | No | `jarvis-chatbot` | LangSmith project name |
| `HOME_ASSISTANT_URL` | No | — | Home Assistant base URL |
| `HOME_ASSISTANT_TOKEN` | No | — | HA long-lived access token |
| `BACKEND_URL` | No | `http://localhost:8000` | Backend URL for Streamlit |

**Never commit `.env` to git.** The `.gitignore` excludes it. CI uses a placeholder key.

---

## Known Issues / Future Work

- `session_histories` in `main.py` is in-memory — lost on restart. Replace with Redis for persistence.
- The `langchain.ipynb` notebook still contains hardcoded API keys in cells 1 and 4 — **revoke those keys if they haven't been already**.
- The notebook uses deprecated LangChain v0.1 imports — it is exploratory only and not imported by the app.
- ChromaDB `chroma_db/` directory is gitignored. In production, back it up or use a hosted vector store (Pinecone, Weaviate).

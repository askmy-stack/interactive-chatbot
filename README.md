# Jarvis — Personal AI Assistant

A production-grade personal AI assistant built with **LangChain v0.3**, **FastAPI**, and **Streamlit**.  
Streams responses token-by-token, remembers conversations across sessions, controls smart home devices, and searches the web in real time.

---

## Features

| Feature | Details |
|---|---|
| **Jarvis Agent** | Tool-calling agent powered by `gpt-4o-mini` |
| **Web Search** | DuckDuckGo — no API key needed |
| **Live Weather** | Open-Meteo free API — any city worldwide |
| **System Monitor** | Real-time CPU, memory, disk via psutil |
| **Smart Home** | Home Assistant REST API (optional) |
| **Streaming** | Token-by-token output via FastAPI + SSE |
| **Vector Memory** | Persistent ChromaDB — memory survives restarts |
| **Observability** | LangSmith tracing + structured JSON logging |
| **Containerised** | One-command deploy with Docker Compose |

---

## Architecture

```
┌──────────────────────┐
│   Streamlit UI       │  :8501
│   app.py             │
└──────────┬───────────┘
           │ HTTP + streaming
┌──────────▼───────────┐
│   FastAPI Backend    │  :8000
│   backend/main.py    │
│                      │
│  ┌────────────────┐  │
│  │ LangChain Agent│  │  gpt-4o-mini + tool-calling
│  │ backend/agent  │  │
│  └───────┬────────┘  │
│          │           │
│  ┌───────▼────────┐  │
│  │    Tools       │  │
│  │ web_search     │  │  DuckDuckGo
│  │ get_weather    │  │  Open-Meteo
│  │ get_system_info│  │  psutil
│  │ control_device │  │  Home Assistant
│  └───────┬────────┘  │
│          │           │
│  ┌───────▼────────┐  │
│  │  ChromaDB      │  │  ./chroma_db (persisted to disk)
│  │  Vector Memory │  │
│  └────────────────┘  │
└──────────────────────┘
```

---

## Quick Start

### Option A — Local

```bash
# 1. Clone
git clone https://github.com/askmy-stack/Interactive-Chatbot.git
cd Interactive-Chatbot

# 2. Install (Python 3.11+)
pip install uv
uv pip install --system .

# 3. Configure
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY at minimum

# 4. Run backend (terminal 1)
uvicorn backend.main:app --reload

# 5. Run UI (terminal 2)
streamlit run app.py
```

Open **http://localhost:8501**

### Option B — Docker (one command)

```bash
cp .env.example .env
# Edit .env and add OPENAI_API_KEY

docker compose up --build
```

Open **http://localhost:8501**

---

## Configuration

Copy `.env.example` to `.env` and fill in the values:

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional — model settings
MODEL_NAME=gpt-4o-mini      # any OpenAI chat model
TEMPERATURE=0.5

# Optional — LangSmith tracing (https://smith.langchain.com)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...

# Optional — Home Assistant smart home
HOME_ASSISTANT_URL=http://192.168.1.100:8123
HOME_ASSISTANT_TOKEN=eyJ...   # Long-Lived Access Token from HA profile
```

---

## Smart Home Setup

1. Open Home Assistant → **Profile** → **Long-Lived Access Tokens** → create one
2. Set `HOME_ASSISTANT_URL` and `HOME_ASSISTANT_TOKEN` in `.env`
3. Restart the backend

Then say:
- *"Turn off the bedroom lights"*
- *"Toggle the living room switch"*
- *"Turn on the fan"*

Supported entity domains: `light`, `switch`, `fan`, `media_player`, `climate`, `cover`

---

## Development

```bash
# Install with dev dependencies
uv pip install --system ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check .

# Type-check
mypy backend/
```

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/chat/stream` | Stream agent response |
| `GET` | `/chat/{id}/history` | Inspect session history |
| `DELETE` | `/chat/{id}` | Clear session |

Interactive docs at **http://localhost:8000/docs**

---

## Tech Stack

- **Python 3.11**
- **FastAPI** — async backend, streaming responses
- **Streamlit** — web UI
- **LangChain v0.3** — agent, tool-calling, LCEL
- **langchain-openai** — `gpt-4o-mini` via `ChatOpenAI`
- **ChromaDB** — local vector store for persistent memory
- **pydantic-settings** — typed, validated config from `.env`
- **structlog** — structured JSON logging
- **psutil** — system resource monitoring
- **duckduckgo-search** — free web search
- **Docker + Compose** — containerised deployment

# A.S.K. (Autonomous System Kernel)

A production-grade personal AI assistant built with **LangChain v0.3**, **FastAPI**, and **Streamlit**.  
Streams responses token-by-token, remembers conversations across sessions, controls smart home devices, and searches the web in real time.

![A.S.K. Demo](assets/jarvis-demo.gif)

> Replace `assets/jarvis-demo.gif` with your recorded product walkthrough for a richer preview.

---

## Features

| Feature | Details |
|---|---|
| **Autonomous System Kernel Agent** | Tool-calling agent with pluggable LLM providers |
| **Free local default** | Ollama + `llama3.2` — no API key required |
| **Calendar Assistant** | Apple Calendar support for today schedule / next event / free slots |
| **Web Search** | DuckDuckGo — no API key needed |
| **Live Weather** | Open-Meteo free API — any city worldwide |
| **System Monitor** | Real-time CPU, memory, disk via psutil |
| **Voice Path** | Voice transcript to response + local TTS endpoint |
| **Smart Home** | Home Assistant REST API (optional) |
| **Streaming** | Token-by-token output via FastAPI + SSE |
| **Vector Memory** | Persistent ChromaDB — memory survives restarts |
| **Memory Graph** | Structured commitments/facts for daily workflow recall |
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
│  │ LangChain Agent│  │  Ollama / OpenAI / OpenRouter
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

### Option A — Local (free with Ollama)

```bash
# 1. Clone
git clone https://github.com/askmy-stack/Autonomous-System-Kernel.git
cd Autonomous-System-Kernel

# 2. Install Ollama and pull a model (one-time)
# https://ollama.com
ollama pull llama3.2
ollama pull nomic-embed-text

# 3. Install (Python 3.11+)
pip install uv
uv pip install --system .

# 4. Configure
cp .env.example .env
# Defaults use Ollama — no paid API key required

# 5. Run backend (terminal 1)
uvicorn backend.main:app --reload

# 6. Run UI (terminal 2)
streamlit run app.py
```

Open **http://localhost:8501**

Try these prompts:
- `What is my calendar today?`
- `What is my next event?`
- `Give me my morning brief`
- `What did I commit to this week?`

### Option B — Docker (one command)

```bash
cp .env.example .env
docker compose up --build
```

Open **http://localhost:8501**

### Option C — OpenAI or OpenRouter (optional paid/hosted)

```bash
cp .env.example .env
# For OpenAI:
#   LLM_PROVIDER=openai
#   OPENAI_API_KEY=sk-...
# For OpenRouter free models:
#   LLM_PROVIDER=openrouter
#   OPENROUTER_API_KEY=sk-or-...
```

---

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```bash
# Provider selection (auto picks OpenAI when OPENAI_API_KEY is set, else Ollama)
LLM_PROVIDER=auto

# Free local defaults
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Optional paid providers
OPENAI_API_KEY=
OPENROUTER_API_KEY=

# Optional — model override for active provider
MODEL_NAME=
TEMPERATURE=0.5

# Optional — LangSmith tracing (https://smith.langchain.com)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...

# Optional — Home Assistant smart home
HOME_ASSISTANT_URL=http://192.168.1.100:8123
HOME_ASSISTANT_TOKEN=eyJ...
```

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `LLM_PROVIDER` | No | `auto` | `auto`, `ollama`, `openai`, or `openrouter` |
| `OLLAMA_MODEL` | No | `llama3.2` | Local chat model via Ollama |
| `OPENAI_API_KEY` | No | — | Enables OpenAI when set (or `LLM_PROVIDER=openai`) |
| `OPENROUTER_API_KEY` | No | — | Enables OpenRouter hosted models |
| `MODEL_NAME` | No | provider default | Override model id for active provider |

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
mypy backend/ --ignore-missing-imports
```

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check (provider + model) |
| `POST` | `/chat/stream` | Stream agent response |
| `POST` | `/voice/chat` | Voice transcript in, response + audio out |
| `POST` | `/voice/tts` | Text to local synthesized speech payload |
| `GET` | `/brief/morning` | Daily brief from calendar + memory graph |
| `GET` | `/metrics` | Basic request counters |
| `POST` | `/ops/backup` | Backup local memory stores |
| `GET` | `/chat/{id}/history` | Inspect session history |
| `DELETE` | `/chat/{id}` | Clear session |

Interactive docs at **http://localhost:8000/docs**

---

## Tech Stack

- **Python 3.11**
- **FastAPI** — async backend, streaming responses
- **Streamlit** — web UI
- **LangChain v0.3** — agent, tool-calling, LCEL
- **langchain-ollama** — local models via Ollama (default)
- **langchain-openai** — optional OpenAI / OpenRouter chat models
- **ChromaDB** — local vector store for persistent memory
- **pydantic-settings** — typed, validated config from `.env`
- **structlog** — structured JSON logging
- **psutil** — system resource monitoring
- **duckduckgo-search** — free web search
- **Docker + Compose** — containerised deployment

---

## Roadmap Snapshot

- [x] FastAPI backend + Streamlit frontend split
- [x] Tool-calling agent with streaming
- [x] Apple Calendar read workflows
- [x] Voice request/response pathway
- [x] Memory graph + morning brief
- [x] Pluggable LLM providers (Ollama default, optional OpenAI/OpenRouter)
- [ ] Native push-to-talk streaming STT
- [ ] Calendar write operations with approval guardrails

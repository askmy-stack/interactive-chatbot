# Local-Only Privacy Mode Runbook

A.S.K. is designed to run fully on your machine with **no paid API keys** and **no cloud LLM calls** when configured for local-only operation.

## Quick checklist

1. Set `LLM_PROVIDER=ollama` (or leave `auto` with no OpenAI/OpenRouter keys).
2. Set `PRIVACY_MODE=local_only` in `.env`.
3. Run Ollama locally: `ollama pull llama3.2` and `ollama pull nomic-embed-text`.
4. Keep `LANGCHAIN_TRACING_V2=false` unless you explicitly want traces sent to LangSmith.
5. Do not set `OPENAI_API_KEY` or `OPENROUTER_API_KEY`.

## What stays local

| Component | Local path | Notes |
|---|---|---|
| Chat model | Ollama (`OLLAMA_BASE_URL`) | Default when no paid keys |
| Embeddings | Ollama `nomic-embed-text` | Used by ChromaDB memory |
| Vector memory | `./chroma_db` | On-disk SQLite + vectors |
| Memory graph | `./memory_graph.db` | SQLite facts/entities |
| Voice TTS | macOS `say` | Optional; empty on Linux CI |
| Voice STT | faster-whisper / whisper CLI | Falls back to browser transcript |
| Calendar | Apple Calendar via AppleScript | macOS only; mocked in CI |

## Network calls in local-only mode

These tools may still reach the public internet (no API key required):

- **DuckDuckGo web search** — only when you ask search questions
- **Open-Meteo weather** — only when you ask for weather

Disable usage by avoiding prompts that trigger those tools, or remove the tools from `backend/agent.py` for air-gapped installs.

## Backups (recommended before upgrades)

```bash
curl -X POST http://localhost:8000/ops/backup
```

Restore:

```bash
curl -X POST http://localhost:8000/ops/restore \
  -H 'Content-Type: application/json' \
  -d '{"backup_path":"./backups/memory_graph.db.YYYYMMDD_HHMMSS.bak","target_path":"./memory_graph.db"}'
```

## Provider health

```bash
curl http://localhost:8000/health/providers
```

If the active provider is unhealthy, set `LLM_PROVIDER=ollama` and confirm Ollama is running.

## Calendar write guardrails

Calendar mutations are **read-only by default**. Writes require:

1. User confirmation in the UI or chat
2. `POST /calendar/approve` with `{"action":"create_event"}` or `update_event`
3. Tool call with the returned `approval_token` (single use, 5-minute TTL)

## Replacing demo media

- Animated preview: record `assets/jarvis-demo.gif` from Streamlit UI
- Static placeholder: `assets/ask-demo.svg` ships until a GIF is recorded

## CI vs macOS

Linux CI runs with mocked calendar/STT and no `say` TTS. macOS local dev gets full Apple Calendar + `say` TTS when available.

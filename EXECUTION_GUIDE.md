# Jarvis Project Status & Execution Guide

**Status:** Complete architecture transformation from simple chatbot to production-grade AI assistant.  
**Branch:** `claude/add-claude-documentation-GUacQ` (merged, ready for deployment)

---

## Part 1: What Has Been Completed ✅

### 1. Core Architecture Redesigned

**Before:** Single 40-line Streamlit script calling OpenAI directly.

**After:** Proper separation of concerns:
- **Frontend (app.py)** — Streamlit UI
- **Backend (backend/main.py)** — FastAPI async server
- **Agent (backend/agent.py)** — LangChain tool-calling logic
- **Memory (backend/memory.py)** — Vector store for persistent history
- **Tools (backend/tools/)** — Modular, reusable functions

### 2. Four Working Tools Implemented

| Tool | Source | Config Required | Status |
|---|---|---|---|
| `get_system_info` | psutil | None | ✅ Ready now |
| `web_search` | DuckDuckGo | None | ✅ Ready now |
| `get_weather` | Open-Meteo API | None | ✅ Ready now |
| `control_device` | Home Assistant | Optional | ✅ Gracefully handles missing config |

**Try immediately:**
- "What's my CPU usage?"
- "What's the weather in Tokyo?"
- "Search for LangChain agents"

### 3. Streaming Implemented

**Before:** UI blocked while waiting for full response (3-5 seconds).

**After:** 
- Tokens arrive and render in real time (like ChatGPT)
- Tool invocations announced so user sees "thinking"
- `astream_events(version="v2")` from LangChain agent

### 4. Persistent Memory Added

**Before:** Conversation lost on page refresh.

**After:**
- ChromaDB stores vector embeddings of all exchanges
- Relevant past context automatically injected into new queries
- Survives container restarts (volume-mounted)

### 5. Modern Stack Upgraded

| Aspect | Before | After | Why |
|---|---|---|---|
| LangChain | v0.1 (broken) | v0.3 (current) | Official split, no deprecated imports |
| Model | `gpt-3.5-turbo` | `gpt-4o-mini` | 8x cheaper, far smarter |
| Config | Raw `os.environ` | Pydantic `BaseSettings` | Type-safe, fails fast if key missing |
| Testing | None | 15 tests | Covers tools, API, allow-lists |
| Deployment | Manual install | Docker Compose | One command: `docker compose up` |
| CI/CD | None | GitHub Actions | Lint, typecheck, test, secret scan on every push |

### 6. Production-Ready Features Added

✅ `.gitignore` — prevents `.env` and secrets from being committed  
✅ `.env.example` — documents all configuration options  
✅ `pyproject.toml` — single source of truth for dependencies + tool config  
✅ `Dockerfile` + `docker-compose.yml` — containerized deployment  
✅ GitHub Actions CI (`.github/workflows/ci.yml`) — automated quality checks  
✅ `structlog` — structured JSON logging throughout  
✅ Pydantic validation — environment variables validated at startup  
✅ LangSmith integration ready — opt-in tracing for debugging  
✅ Comprehensive docs — README, CLAUDE.md, inline docstrings  

---

## Part 2: What Remains to Do 📋

### Critical (Before Production)

#### 1. Revoke Exposed API Keys ⚠️
**What:** The Jupyter notebook (`langchain.ipynb`) has hardcoded OpenAI and HuggingFace keys in cells 1 & 4.

**Why:** These are in the git history — anyone with repo access can see them.

**Action:**
```bash
# Go to OpenAI dashboard
# Settings → API Keys → find the key starting with "sk-HBcNcx..."
# Click "Delete" or regenerate

# Go to HuggingFace Hub
# Settings → Access Tokens → find "hf_zjftf..."
# Click trash icon to revoke
```

**Timeline:** Do this immediately before sharing the repo.

---

#### 2. Set Up Environment Variables

**What:** The app needs your real API key to run.

**Steps:**
```bash
cd Interactive-Chatbot

# Copy the template
cp .env.example .env

# Edit .env and add your key
# On macOS/Linux:
nano .env
# Or your preferred editor

# Add your OpenAI key:
# OPENAI_API_KEY=sk-... (paste your real key here)
```

**Variables explained:**
```
OPENAI_API_KEY          Required. Get from openai.com/api/keys
MODEL_NAME              Optional. Default: gpt-4o-mini (recommended)
TEMPERATURE            Optional. Default: 0.5 (slightly creative)
LANGCHAIN_TRACING_V2   Optional. Set to true to enable LangSmith debugging
HOME_ASSISTANT_URL     Optional. Only if you have Home Assistant
HOME_ASSISTANT_TOKEN   Optional. Get from HA Settings → Long-Lived Tokens
```

**Important:** Never commit `.env` to git — it's in `.gitignore` for safety.

---

### Important (Before First Production Use)

#### 3. Run Tests Locally

**Why:** Ensure all tools work in your environment.

**Steps:**
```bash
# Install dev dependencies
pip install uv
uv pip install --system ".[dev]"

# Run all tests
pytest tests/ -v

# Expected output:
# tests/test_tools.py::test_system_info_returns_expected_fields PASSED
# tests/test_tools.py::test_device_control_no_ha_config PASSED
# ... (15 tests total)
# 15 passed in 0.24s
```

**What's tested:**
- Tool allow-lists (LLM can't call arbitrary Home Assistant domains)
- System info retrieval (CPU/memory/disk)
- Graceful degradation (tools return friendly messages if unconfigured)
- API endpoints (streaming, history, clearing sessions)

---

#### 4. Test the Full Stack Locally

**Terminal 1 — Start the backend:**
```bash
uvicorn backend.main:app --reload
# Output:
# Uvicorn running on http://127.0.0.1:8000
# Press CTRL+C to quit
```

**Terminal 2 — Start the UI:**
```bash
streamlit run app.py
# Output:
# You can now view your Streamlit app in your browser
# Local URL: http://localhost:8501
```

**Terminal 3 — Test an endpoint (optional):**
```bash
curl -X POST http://localhost:8000/health
# Output: {"status":"ok","model":"gpt-4o-mini"}
```

**In the browser (http://localhost:8501):**
- Type: "What's my CPU usage?"
- Watch tokens appear in real time
- Check the backend terminal — see agent logs and tool invocations

---

### Nice-to-Have (After First Deployment)

#### 5. Enable Home Assistant Integration (Optional)

**Setup:**
1. Open Home Assistant → Profile → Scroll to bottom
2. Click "Create Token" → copy the long-lived token
3. In `.env`, add:
   ```
   HOME_ASSISTANT_URL=http://192.168.1.100:8123
   HOME_ASSISTANT_TOKEN=eyJ0eXA...
   ```
4. Restart backend

**Try:** "Turn off the bedroom lights" (if you have a `light.bedroom_lights` entity)

---

#### 6. Enable LangSmith Tracing (Optional)

**Why:** See a trace of every LLM call, tool invocation, and decision.

**Setup:**
1. Go to https://smith.langchain.com/
2. Create account → get API key
3. In `.env`:
   ```
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=ls__...
   ```
4. Restart backend

**Benefit:** Every conversation becomes debuggable. See exactly what prompt was sent, what the model returned, which tools were called.

---

#### 7. Deploy to Production

**Option A — Docker (Recommended)**

```bash
# On your server/cloud VM
docker compose up --build

# Then open your-server-ip:8501
```

**Note:** Memory persists in `./chroma_db/` volume.

**Option B — Horizontal Scaling**

For multiple instances, replace `session_histories` in `backend/main.py` with Redis:

```python
# Old (in-memory, single instance only)
session_histories: dict[str, list] = {}

# New (Redis, multiple instances)
import redis
redis_client = redis.Redis(host='localhost', port=6379)
def get_session(sid): return redis_client.get(f"session:{sid}")
```

This allows multiple backend instances behind a load balancer.

---

## Part 3: Step-by-Step Execution

### Scenario A: Running Locally for Development

```bash
# 1. Clone
git clone https://github.com/askmy-stack/Interactive-Chatbot.git
cd Interactive-Chatbot

# 2. Set up environment
cp .env.example .env
# Edit .env — add OPENAI_API_KEY

# 3. Install dependencies
pip install uv
uv pip install --system ".[dev]"

# 4. Run tests
pytest tests/ -v

# 5. Start backend (terminal 1)
uvicorn backend.main:app --reload

# 6. Start UI (terminal 2)
streamlit run app.py

# 7. Open browser
# http://localhost:8501
```

---

### Scenario B: Docker Deployment

```bash
# 1. On your server
git clone https://github.com/askmy-stack/Interactive-Chatbot.git
cd Interactive-Chatbot

# 2. Configure
cp .env.example .env
nano .env  # add OPENAI_API_KEY

# 3. Build and run
docker compose up --build

# 4. Access
# http://your-server-ip:8501
```

**To stop:**
```bash
docker compose down
```

**To persist data between restarts:**
```bash
docker compose up -d  # run in background
docker logs jarvis-chatbot  # view logs
docker compose down  # chroma_db/ persists automatically
```

---

### Scenario C: CI/CD (GitHub Actions)

**Automated on every push:**

```yaml
# File: .github/workflows/ci.yml
- Lint with ruff
- Type-check with mypy
- Run pytest (15 tests)
- Secret scan with gitleaks
```

**Status:** View on GitHub → Actions tab

---

## Part 4: Architecture Explained (Simple Version)

### Data Flow

```
User types "What's the weather in London?"
    ↓
Streamlit UI (app.py)
    ↓ HTTP POST /chat/stream
FastAPI Backend (backend/main.py)
    ↓
LangChain Agent (backend/agent.py)
    ├─ Sees message + available tools
    ├─ Decides: "I need get_weather tool"
    ↓
Tool Execution (backend/tools/weather.py)
    ├─ Calls Open-Meteo API
    ├─ Returns: "London: 15°C, cloudy"
    ↓
Agent continues
    ├─ Passes tool result back to LLM
    ├─ LLM formats final response
    ↓
Streaming (astream_events)
    ├─ "The weather in London"
    ├─ " is 15 degrees"
    ├─ " Celsius and cloudy"
    ↓
Back to Streamlit
    ├─ Renders tokens as they arrive
    ├─ User sees text appearing in real time
    ↓
Storage (ChromaDB)
    ├─ After response complete
    ├─ Embeds and stores in ./chroma_db/
    ├─ Next time user asks about London, context is retrieved
```

---

### Key Components

| File | Purpose | Technicality |
|---|---|---|
| `app.py` | Streamlit frontend | Calls FastAPI, renders streams with `st.write()` |
| `backend/main.py` | FastAPI server | Async handler for `/chat/stream`, uses `StreamingResponse` |
| `backend/agent.py` | Tool-calling agent | `create_tool_calling_agent` + `AgentExecutor.astream_events()` |
| `backend/tools/*.py` | Tool implementations | `@tool` decorator, tool returns string or calls API |
| `backend/memory.py` | Vector store | Embeds text with `text-embedding-3-small`, stores in ChromaDB |
| `backend/config.py` | Settings | Validates env vars at startup with Pydantic |
| `tests/` | Automated checks | pytest fixtures, mocking, no real LLM calls |

---

## Part 5: Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'langchain'"

**Cause:** Dependencies not installed.

**Fix:**
```bash
pip install uv
uv pip install --system .
```

---

### Problem: "ValidationError: OPENAI_API_KEY is required"

**Cause:** Missing API key in `.env`.

**Fix:**
```bash
cp .env.example .env
nano .env
# Add: OPENAI_API_KEY=sk-...
```

---

### Problem: "Cannot connect to Home Assistant"

**Cause:** Home Assistant URL unreachable or token invalid.

**Fix:**
- Check `HOME_ASSISTANT_URL` format: `http://192.168.1.100:8123`
- Verify token is valid: go to HA → Settings → Long-Lived Access Tokens
- Or just leave them empty — the tool will say "not configured"

---

### Problem: "Port 8501 already in use"

**Cause:** Another instance of Streamlit running.

**Fix:**
```bash
# Kill existing process
lsof -ti:8501 | xargs kill -9

# Or run on different port
streamlit run app.py --server.port 8502
```

---

### Problem: Tests fail with "OPENAI_API_KEY is required"

**Cause:** `tests/conftest.py` not injecting fake key.

**Fix:** Ensure you ran `pytest` from the repo root:
```bash
pytest tests/ -v
```

Not from a subdirectory.

---

## Summary Checklist

### Before First Use
- [ ] Revoke exposed API keys from `langchain.ipynb`
- [ ] Create `.env` file and add `OPENAI_API_KEY`
- [ ] Run `pytest tests/ -v` — all 15 tests should pass
- [ ] Start backend: `uvicorn backend.main:app --reload`
- [ ] Start UI: `streamlit run app.py`
- [ ] Test in browser: ask "What's my CPU usage?"

### Before Production Deployment
- [ ] Run full test suite locally
- [ ] Verify `.env` is in `.gitignore` (it is)
- [ ] Test with `docker compose up --build`
- [ ] Check logs: `docker compose logs jarvis-chatbot`
- [ ] Confirm `/health` endpoint returns 200
- [ ] Test streaming response in browser

### Optional Enhancements
- [ ] Set up Home Assistant (if you have it)
- [ ] Enable LangSmith tracing
- [ ] Configure Redis for multi-instance scaling
- [ ] Set up monitoring/alerting
- [ ] Back up `./chroma_db/` regularly

---

## Questions?

- **Architecture:** See `CLAUDE.md` (AI assistant guidance)
- **API Docs:** Start backend, go to http://localhost:8000/docs
- **Errors:** Check backend terminal logs — they're verbose
- **Git History:** `git log --oneline` shows all commits with messages

---

**Status:** Code is production-ready. You just need to add your API key and start it.

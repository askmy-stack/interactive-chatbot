# A.S.K. Integration Guide

A.S.K. supports three deployment modes so you can run it as a full product, a background daemon, or an embedded API behind your own UI.

## Deployment Modes

### Standalone (default)

Full Next.js web UI + FastAPI backend. Best for personal use.

```bash
# Terminal 1 — API
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Web UI
cd frontend && npm run dev
```

Open http://localhost:3000

### Sidecar

API runs as a background daemon; your app connects via SDK.

```bash
ASK_DEPLOYMENT_MODE=sidecar uvicorn backend.main:app --port 8000
```

Your app uses the TypeScript or Python SDK to call `/chat`, `/voice/chat`, and brief endpoints.

### Embedded

API only. CORS is locked to your app's origin.

```bash
ASK_DEPLOYMENT_MODE=embedded \
ASK_EXTERNAL_APP_ORIGIN=https://myapp.example.com \
ASK_API_KEY=your-secret-key \
uvicorn backend.main:app --port 8000
```

---

## Channel Routing

A.S.K. enforces mode-matched I/O:

| Input | Output | Endpoint |
|---|---|---|
| Text | Text (no TTS) | `POST /chat` or `/chat/stream` |
| Voice | Voice (TTS audio) | `POST /voice/chat` |

Set `input_channel` and `output_channel` on every request. The web UI's `channel-router.ts` handles this automatically.

---

## SDK Usage

### TypeScript

```typescript
import { AskClient } from "./sdk/typescript";

const ask = new AskClient({
  baseUrl: "http://localhost:8000",
  apiKey: process.env.ASK_API_KEY,
  client: "external-app",
});

// Text chat
const reply = await ask.chat("What's on my calendar?", "session-1");
console.log(reply.response);

// Voice chat
const voice = await ask.voiceChat("What's the weather?", "session-1");
if (voice.tts?.tts_available) {
  playAudio(voice.tts.audio_base64);
}

// Briefs
const brief = await ask.morningBrief();
```

### Python

```python
from sdk.python.ask_client import AskClient

ask = AskClient(base_url="http://localhost:8000", api_key="your-key")
reply = ask.chat("Hello", session_id="s1")
print(reply["response"])
```

---

## Authentication

Set `ASK_API_KEY` in the API environment. Pass it as a Bearer token:

```
Authorization: Bearer <ASK_API_KEY>
```

---

## CORS

For embedded mode, set `ASK_EXTERNAL_APP_ORIGIN` to your app's URL. The API allows `localhost:3000` by default for local development.

---

## Example Integration

See `examples/integrate-with-external-app/` for a minimal Node.js demo that calls the API directly.

---

## Legacy Streamlit UI

The Streamlit UI (`app.py`) is deprecated. Enable with:

```bash
ENABLE_LEGACY_STREAMLIT=true streamlit run app.py
```

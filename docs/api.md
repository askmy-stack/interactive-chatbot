# A.S.K. API Reference

Base URL: `http://localhost:8000` (default)

## Authentication

When `ASK_API_KEY` is set, all endpoints except `/health*` require:

```
Authorization: Bearer <ASK_API_KEY>
```

## Client Identification

Send `X-ASK-Client` on every request:

| Value | Description |
|---|---|
| `standalone-web` | A.S.K. Next.js UI |
| `external-app` | Third-party integration |
| `cli` | Command-line client |

## Deployment Modes

| Mode | Description |
|---|---|
| `standalone` | Full web UI + API (default) |
| `sidecar` | API daemon; external app owns UI |
| `embedded` | API only; CORS locked to `ASK_EXTERNAL_APP_ORIGIN` |

---

## Health

### `GET /health`

Liveness check with provider, model, deployment mode, and TTS status.

### `GET /health/providers`

Probe Ollama/OpenAI/OpenRouter availability.

---

## Chat (text-in → text-out)

### `POST /chat/stream`

SSE stream. No TTS is produced.

**Request:**
```json
{
  "message": "What's on my calendar?",
  "session_id": "user-123",
  "input_channel": "text",
  "output_channel": "text"
}
```

**SSE events:**
1. `meta` — session and channel info
2. `token` — incremental response chunks
3. `done` — final envelope with full response

### `POST /chat`

Non-streaming text chat (SDK-friendly).

**Response envelope:**
```json
{
  "session_id": "user-123",
  "input_channel": "text",
  "output_channel": "text",
  "response": "Your next meeting is at 2pm."
}
```

---

## Voice (voice-in → voice-out)

### `POST /voice/chat`

Transcript in, agent response + TTS audio out.

**Request:**
```json
{
  "transcript": "What's the weather?",
  "session_id": "user-123",
  "input_channel": "voice",
  "output_channel": "voice"
}
```

**Response envelope:**
```json
{
  "session_id": "user-123",
  "input_channel": "voice",
  "output_channel": "voice",
  "transcript": "What's the weather?",
  "response": "It's 72°F and sunny.",
  "tts": {
    "tts_available": true,
    "tts_provider": "macos-say",
    "audio_base64": "..."
  }
}
```

When TTS is unavailable:
```json
{
  "tts": {
    "tts_available": false,
    "tts_unavailable_reason": "No TTS backend available"
  }
}
```

### `POST /voice/tts`

Synthesize speech from text.

### `GET /voice/tts/status`

List available TTS providers.

### `POST /voice/stt/transcribe`

Transcribe audio (base64) or accept browser transcript fallback.

### `GET /voice/stt/status`

List available STT backends.

---

## Briefs

| Endpoint | Description |
|---|---|
| `GET /brief/morning` | Morning brief |
| `GET /brief/eod` | End-of-day recap |
| `GET /brief/next-day` | Next-day prep |
| `GET /brief/reminders` | Proactive reminders |

---

## Calendar

### `POST /calendar/approve`

Request approval token for calendar mutations.

```json
{ "action": "create_event" }
```

---

## Session Management

| Endpoint | Description |
|---|---|
| `GET /chat/{session_id}/history` | Get session history |
| `DELETE /chat/{session_id}` | Clear session |

---

## Memory Graph

| Endpoint | Description |
|---|---|
| `GET /memory/graph/summary` | Graph summary |
| `POST /memory/graph/entity` | Add entity |
| `POST /memory/graph/fact` | Add fact |

---

## Operations

| Endpoint | Description |
|---|---|
| `GET /metrics` | Request counters |
| `POST /ops/backup` | Backup databases |
| `POST /ops/restore` | Restore from backup |

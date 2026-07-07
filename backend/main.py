"""
A.S.K. (Autonomous System Kernel) FastAPI backend.

Endpoints:
  GET  /health              — liveness check
  POST /chat/stream         — stream agent response (text/plain chunked)
  DELETE /chat/{session_id} — clear in-memory session history

Session history lives in a plain dict for simplicity.
For horizontal scaling, swap `session_histories` for a Redis-backed store.
"""

from __future__ import annotations

import os

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from backend.config import settings
from backend.memory_graph import MemoryGraph
from backend.ops import backup_file
from backend.providers import effective_model_name, resolve_provider
from backend.voice.service import VoiceService
from backend.workflows.daily_brief import build_morning_brief

# Enable LangSmith tracing if configured
if settings.langchain_tracing_v2 and settings.langchain_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

log = structlog.get_logger()

app = FastAPI(
    title="A.S.K. API",
    version="1.0.0",
    description="Personal AI assistant backend with tool-calling, vector memory, and streaming.",
)

# In-memory session store: {session_id: [BaseMessage, ...]}
# Each entry is a LangChain message list used as chat_history for the agent.
session_histories: dict[str, list] = {}
voice_service = VoiceService()
memory_graph = MemoryGraph()
metrics: dict[str, int] = {"chat_requests": 0, "voice_requests": 0}


async def astream_response(user_input: str, session_id: str, chat_history: list):
    """
    Lazy proxy so tests can patch `backend.main.astream_response` without importing
    the full agent stack at module import time.
    """
    from backend.agent import astream_response as _astream_response

    async for token in _astream_response(user_input, session_id, chat_history):
        yield token


# ── Request/Response schemas ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class VoiceChatRequest(BaseModel):
    transcript: str
    session_id: str = "default"


class TtsRequest(BaseModel):
    text: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Liveness check — surfaces the active provider and model."""
    return {
        "status": "ok",
        "provider": resolve_provider(),
        "model": effective_model_name(),
    }


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    Stream an agent response token-by-token.

    The response body is plain text with chunks arriving as the LLM generates them.
    Tool-use announcements are interspersed so the caller can see the assistant thinking.

    Session history is updated after the full response is assembled.
    The exchange is also saved to the ChromaDB long-term memory store.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")
    metrics["chat_requests"] += 1

    history = session_histories.get(req.session_id, [])

    async def generate():
        full_response = ""
        try:
            async for token in astream_response(req.message, req.session_id, history):
                full_response += token
                yield token
        except Exception as exc:
            error_msg = f"[Error: {exc}]"
            log.error("agent_error", session_id=req.session_id, error=str(exc))
            yield error_msg
            full_response = error_msg

        # Persist to in-memory session history for next turn
        session_histories[req.session_id] = history + [
            HumanMessage(content=req.message),
            AIMessage(content=full_response),
        ]

    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/voice/chat")
async def voice_chat(req: VoiceChatRequest):
    """Accept transcript text, run assistant response, and return TTS audio payload."""
    metrics["voice_requests"] += 1
    transcript = voice_service.transcribe_text(req.transcript)
    if not transcript:
        raise HTTPException(status_code=400, detail="transcript must not be empty")
    history = session_histories.get(req.session_id, [])
    full_response = ""
    async for token in astream_response(transcript, req.session_id, history):
        full_response += token
    session_histories[req.session_id] = history + [
        HumanMessage(content=transcript),
        AIMessage(content=full_response),
    ]
    audio_b64 = voice_service.synthesize(full_response)
    return {"transcript": transcript, "response": full_response, "audio_base64": audio_b64}


@app.post("/voice/tts")
def voice_tts(req: TtsRequest):
    """Synthesize speech from text."""
    return {"audio_base64": voice_service.synthesize(req.text)}


@app.delete("/chat/{session_id}")
def clear_session(session_id: str):
    """Clear in-memory chat history for a session."""
    session_histories.pop(session_id, None)
    log.info("session_cleared", session_id=session_id)
    return {"cleared": session_id}


@app.get("/chat/{session_id}/history")
def get_history(session_id: str):
    """Return the raw message history for a session (useful for debugging)."""
    history = session_histories.get(session_id, [])
    return {
        "session_id": session_id,
        "turn_count": len(history) // 2,
        "messages": [
            {"role": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content}
            for m in history
        ],
    }


@app.get("/brief/morning")
def morning_brief():
    return {"brief": build_morning_brief(memory_graph)}


@app.get("/metrics")
def get_metrics():
    return metrics


@app.post("/ops/backup")
def create_backup():
    chroma_backup = backup_file("./chroma_db/chroma.sqlite3")
    graph_backup = backup_file("./memory_graph.db")
    return {
        "privacy_mode": settings.privacy_mode,
        "chroma_backup": chroma_backup,
        "graph_backup": graph_backup,
    }

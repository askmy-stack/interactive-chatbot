"""
A.S.K. (Autonomous System Kernel) FastAPI backend.

Endpoints:
  GET  /health              — liveness check
  POST /chat/stream         — stream agent response (SSE with meta + tokens)
  POST /voice/chat          — voice-in → voice-out with TTS
  DELETE /chat/{session_id} — clear in-memory session history

Session history lives in a plain dict for simplicity.
For horizontal scaling, swap `session_histories` for a Redis-backed store.
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage

from backend.calendar_approval import approval_store
from backend.config import settings
from backend.memory_graph import Entity, EntityType, Fact, MemoryGraph
from backend.middleware import ApiKeyMiddleware, ClientHeaderMiddleware, configure_cors
from backend.ops import backup_file, list_backups, restore_file
from backend.providers import effective_model_name, resolve_provider
from backend.providers.health import check_all_providers
from backend.schemas import (
    CalendarApproveRequest,
    ChatEnvelope,
    ChatRequest,
    EntityRequest,
    RestoreRequest,
    StreamMeta,
    SttTranscribeRequest,
    TtsInfo,
    TtsRequest,
    VoiceChatRequest,
)
from backend.voice.service import VoiceService
from backend.voice.stt import decode_audio_payload
from backend.workflows.daily_brief import build_morning_brief
from backend.workflows.eod_recap import build_eod_recap, build_next_day_prep
from backend.workflows.reminders import build_proactive_reminders

# Enable LangSmith tracing if configured
if settings.langchain_tracing_v2 and settings.langchain_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

log = structlog.get_logger()

app = FastAPI(
    title="A.S.K. API",
    version="1.2.0",
    description="Personal AI assistant backend with tool-calling, vector memory, and streaming.",
)

configure_cors(app)
app.add_middleware(ClientHeaderMiddleware)
app.add_middleware(ApiKeyMiddleware)

# In-memory session store: {session_id: [BaseMessage, ...]}
session_histories: dict[str, list] = {}
voice_service = VoiceService()
memory_graph = MemoryGraph()
metrics: dict[str, int] = {
    "chat_requests": 0,
    "voice_requests": 0,
    "stt_requests": 0,
}


async def astream_response(user_input: str, session_id: str, chat_history: list):
    """
    Lazy proxy so tests can patch `backend.main.astream_response` without importing
    the full agent stack at module import time.
    """
    from backend.agent import astream_response as _astream_response

    async for token in _astream_response(user_input, session_id, chat_history):
        yield token


def _build_tts_info(tts_result, *, include_audio: bool) -> TtsInfo:
    return TtsInfo(
        tts_available=tts_result.available,
        tts_provider=tts_result.provider if tts_result.available else None,
        tts_unavailable_reason=tts_result.unavailable_reason,
        audio_base64=tts_result.audio_base64 if include_audio and tts_result.available else None,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health(request: Request):
    """Liveness check — surfaces the active provider and model."""
    return {
        "status": "ok",
        "provider": resolve_provider(),
        "model": effective_model_name(),
        "privacy_mode": settings.privacy_mode,
        "deployment_mode": settings.ask_deployment_mode,
        "client": getattr(request.state, "ask_client", "external-app"),
        "tts": voice_service.tts_status(),
    }


@app.get("/health/providers")
def health_providers():
    """Probe Ollama/OpenAI/OpenRouter and suggest fallback order."""
    return check_all_providers()


@app.get("/voice/stt/status")
def voice_stt_status():
    """Return available STT backends for graceful UI fallback."""
    return voice_service.stt_status()


@app.get("/voice/tts/status")
def voice_tts_status():
    """Return available TTS backends."""
    return voice_service.tts_status()


@app.post("/voice/stt/transcribe")
def voice_stt_transcribe(req: SttTranscribeRequest):
    """Transcribe uploaded audio; falls back to validated browser transcript."""
    metrics["stt_requests"] += 1
    if req.audio_base64:
        try:
            audio_bytes = decode_audio_payload(req.audio_base64)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"invalid audio payload: {exc}") from exc
        result = voice_service.transcribe_audio(audio_bytes, mime_type=req.mime_type)
        if result.text:
            return {"text": result.text, "backend": result.backend, "confidence": result.confidence}
    if req.browser_transcript.strip():
        result = voice_service.stt.validate_browser_transcript(req.browser_transcript)
        return {"text": result.text, "backend": result.backend, "confidence": result.confidence}
    return {
        "text": "",
        "backend": "unavailable",
        "confidence": None,
        "detail": "No local STT backend available. Send browser_transcript as fallback.",
    }


@app.websocket("/voice/stt/stream")
async def voice_stt_stream(websocket: WebSocket):
    """Chunked audio STT over WebSocket. Send JSON {audio_base64, mime_type, final: bool}."""
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            audio_b64 = payload.get("audio_base64", "")
            mime_type = payload.get("mime_type", "audio/wav")
            browser_transcript = payload.get("browser_transcript", "")
            is_final = bool(payload.get("final", True))

            if audio_b64:
                audio_bytes = decode_audio_payload(audio_b64)
                result = voice_service.transcribe_audio(audio_bytes, mime_type=mime_type)
            elif browser_transcript:
                result = voice_service.stt.validate_browser_transcript(browser_transcript)
            else:
                result = voice_service.stt.validate_browser_transcript("")

            await websocket.send_json(
                {
                    "text": result.text,
                    "backend": result.backend,
                    "confidence": result.confidence,
                    "final": is_final,
                }
            )
            if is_final:
                break
    except WebSocketDisconnect:
        log.info("stt_stream_disconnected")
    except Exception as exc:
        await websocket.send_json({"error": str(exc)})
        await websocket.close()


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    """Stream an agent response. Text-in → text-out (no TTS)."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")
    if req.output_channel == "voice":
        raise HTTPException(
            status_code=400,
            detail="text chat endpoint does not produce voice output; use /voice/chat",
        )

    metrics["chat_requests"] += 1
    input_channel = req.input_channel
    output_channel = req.output_channel
    session_id = req.session_id
    history = session_histories.get(session_id, [])
    client = getattr(request.state, "ask_client", "external-app")

    async def generate() -> AsyncIterator[str]:
        meta = StreamMeta(
            session_id=session_id,
            input_channel=input_channel,
            output_channel=output_channel,
        )
        yield f"data: {json.dumps(meta.model_dump())}\n\n"

        full_response = ""
        try:
            async for token in astream_response(req.message, session_id, history):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        except Exception as exc:
            error_msg = f"[Error: {exc}]"
            log.error("agent_error", session_id=session_id, error=str(exc))
            full_response = error_msg
            yield f"data: {json.dumps({'type': 'token', 'content': error_msg})}\n\n"

        session_histories[session_id] = history + [
            HumanMessage(content=req.message),
            AIMessage(content=full_response),
        ]

        done = {
            "type": "done",
            "session_id": session_id,
            "input_channel": input_channel,
            "output_channel": output_channel,
            "response": full_response,
            "client": client,
        }
        yield f"data: {json.dumps(done)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/chat")
async def chat_sync(req: ChatRequest, request: Request):
    """Non-streaming text chat for SDK consumers."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    metrics["chat_requests"] += 1
    history = session_histories.get(req.session_id, [])
    full_response = ""
    async for token in astream_response(req.message, req.session_id, history):
        full_response += token

    session_histories[req.session_id] = history + [
        HumanMessage(content=req.message),
        AIMessage(content=full_response),
    ]

    envelope = ChatEnvelope(
        session_id=req.session_id,
        input_channel=req.input_channel,
        output_channel=req.output_channel,
        response=full_response,
    )
    return JSONResponse(content=envelope.model_dump())


@app.post("/voice/chat")
async def voice_chat(req: VoiceChatRequest, request: Request):
    """Voice-in → voice-out: transcript → agent response → TTS audio."""
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

    tts_result = voice_service.synthesize(full_response)
    tts_info = _build_tts_info(tts_result, include_audio=True)

    envelope = ChatEnvelope(
        session_id=req.session_id,
        input_channel=req.input_channel,
        output_channel=req.output_channel,
        response=full_response,
        transcript=transcript,
        tts=tts_info,
    )
    return JSONResponse(content=envelope.model_dump())


@app.post("/voice/tts")
def voice_tts(req: TtsRequest):
    """Synthesize speech from text."""
    tts_result = voice_service.synthesize(req.text)
    return {
        "audio_base64": tts_result.audio_base64,
        "tts_available": tts_result.available,
        "tts_provider": tts_result.provider,
        "tts_unavailable_reason": tts_result.unavailable_reason,
    }


@app.post("/calendar/approve")
def calendar_approve(req: CalendarApproveRequest):
    """Issue a short-lived approval token required for calendar mutations."""
    if req.action not in {"create_event", "update_event"}:
        raise HTTPException(status_code=400, detail="action must be create_event or update_event")
    grant = approval_store.request_approval(req.action)
    return {
        "approval_token": grant.token,
        "action": grant.action,
        "expires_in_seconds": approval_store.ttl_seconds,
        "message": "User must confirm this action before the token is used.",
    }


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


@app.get("/brief/eod")
def eod_brief():
    return {"brief": build_eod_recap(memory_graph)}


@app.get("/brief/next-day")
def next_day_brief():
    return {"brief": build_next_day_prep(memory_graph)}


@app.get("/brief/reminders")
def reminders_brief():
    return {"brief": build_proactive_reminders()}


@app.get("/memory/graph/summary")
def memory_graph_summary():
    return memory_graph.summary()


@app.post("/memory/graph/entity")
def add_memory_entity(req: EntityRequest):
    try:
        entity_type = EntityType(req.entity_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid entity_type") from exc
    entity_id = memory_graph.add_entity(
        Entity(
            entity_type=entity_type,
            name=req.name,
            attributes=req.attributes,
            source=req.source,
        )
    )
    return {"id": entity_id, "entity_type": req.entity_type, "name": req.name}


@app.post("/memory/graph/fact")
def add_memory_fact(key: str, value: str, source: str = "api"):
    memory_graph.add_fact(Fact(key=key, value=value, source=source))
    return {"stored": True, "key": key}


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
        "backups": list_backups(),
    }


@app.post("/ops/restore")
def restore_backup(req: RestoreRequest):
    restored = restore_file(req.backup_path, req.target_path)
    if not restored:
        raise HTTPException(status_code=400, detail="restore failed — check backup_path")
    return {"restored": restored, "target": req.target_path}

"""Shared API request/response schemas for channel-aware chat."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

InputChannel = Literal["text", "voice"]
OutputChannel = Literal["text", "voice"]
AskClient = Literal["standalone-web", "external-app", "cli"]
DeploymentMode = Literal["standalone", "sidecar", "embedded"]


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    input_channel: InputChannel = "text"
    output_channel: OutputChannel = "text"


class VoiceChatRequest(BaseModel):
    transcript: str
    session_id: str = "default"
    input_channel: InputChannel = "voice"
    output_channel: OutputChannel = "voice"
    audio_base64: str = ""


class TtsRequest(BaseModel):
    text: str


class SttTranscribeRequest(BaseModel):
    audio_base64: str
    mime_type: str = "audio/wav"
    browser_transcript: str = ""


class CalendarApproveRequest(BaseModel):
    action: str = Field(description="create_event or update_event")


class RestoreRequest(BaseModel):
    backup_path: str
    target_path: str


class EntityRequest(BaseModel):
    entity_type: str
    name: str
    attributes: str = ""
    source: str = "api"


class TtsInfo(BaseModel):
    tts_available: bool
    tts_provider: str | None = None
    tts_unavailable_reason: str | None = None
    audio_base64: str | None = None


class ChatEnvelope(BaseModel):
    """Standard response envelope for chat/voice endpoints."""

    session_id: str
    input_channel: InputChannel
    output_channel: OutputChannel
    response: str
    transcript: str | None = None
    tts: TtsInfo | None = None


class StreamMeta(BaseModel):
    """Metadata sent as first SSE event for text streaming."""

    type: str = "meta"
    session_id: str
    input_channel: InputChannel
    output_channel: OutputChannel

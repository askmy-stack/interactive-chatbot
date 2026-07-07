/**
 * Channel router — enforces mode-matched I/O.
 * Text-in → text-out (SSE, no TTS)
 * Voice-in → voice-out (TTS audio playback)
 */

import { streamChat, voiceChat, type ChatEnvelope, type TimelineMessage } from "./ask-client";
import { playAudioBase64, stopAudio } from "./audio";

export type ChannelMode = "text" | "voice";

export interface ChannelResult {
  userMessage: TimelineMessage;
  assistantMessage: TimelineMessage;
  ttsUnavailable?: string;
}

function makeId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export async function sendTextMessage(
  text: string,
  sessionId: string,
  onToken?: (token: string) => void
): Promise<ChannelResult> {
  const userMsg: TimelineMessage = {
    id: makeId(),
    role: "user",
    content: text,
    channel: "text",
    timestamp: Date.now(),
  };

  let fullResponse = "";
  for await (const event of streamChat(text, sessionId)) {
    if (event.type === "token" && event.content) {
      fullResponse += event.content;
      onToken?.(event.content);
    }
    if (event.type === "done" && event.response) {
      fullResponse = event.response;
    }
  }

  const assistantMsg: TimelineMessage = {
    id: makeId(),
    role: "assistant",
    content: fullResponse,
    channel: "text",
    timestamp: Date.now(),
  };

  return { userMessage: userMsg, assistantMessage: assistantMsg };
}

export async function sendVoiceMessage(
  transcript: string,
  sessionId: string
): Promise<ChannelResult & { envelope: ChatEnvelope }> {
  const userMsg: TimelineMessage = {
    id: makeId(),
    role: "user",
    content: transcript,
    channel: "voice",
    timestamp: Date.now(),
  };

  const envelope = await voiceChat(transcript, sessionId);

  const assistantMsg: TimelineMessage = {
    id: makeId(),
    role: "assistant",
    content: envelope.response,
    channel: "voice",
    timestamp: Date.now(),
  };

  let ttsUnavailable: string | undefined;
  if (envelope.tts?.tts_available && envelope.tts.audio_base64) {
    await playAudioBase64(envelope.tts.audio_base64);
  } else {
    ttsUnavailable = envelope.tts?.tts_unavailable_reason ?? "TTS unavailable";
  }

  return { userMessage: userMsg, assistantMessage: assistantMsg, envelope, ttsUnavailable };
}

export { stopAudio };

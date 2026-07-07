/**
 * A.S.K. API client for the standalone web UI.
 */

const API_BASE = process.env.NEXT_PUBLIC_ASK_API_URL || "/api";

export type InputChannel = "text" | "voice";
export type OutputChannel = "text" | "voice";

export interface TimelineMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  channel: InputChannel;
  timestamp: number;
}

export interface TtsInfo {
  tts_available: boolean;
  tts_provider?: string;
  tts_unavailable_reason?: string;
  audio_base64?: string;
}

export interface ChatEnvelope {
  session_id: string;
  input_channel: InputChannel;
  output_channel: OutputChannel;
  response: string;
  transcript?: string;
  tts?: TtsInfo;
}

export interface HealthInfo {
  status: string;
  provider: string;
  model: string;
  deployment_mode: string;
  tts: { tts_available: boolean; providers: string[] };
}

function headers(): Record<string, string> {
  const h: Record<string, string> = {
    "Content-Type": "application/json",
    "X-ASK-Client": "standalone-web",
  };
  const apiKey = process.env.NEXT_PUBLIC_ASK_API_KEY;
  if (apiKey) h["Authorization"] = `Bearer ${apiKey}`;
  return h;
}

export async function fetchHealth(): Promise<HealthInfo> {
  const res = await fetch(`${API_BASE}/health`, { headers: headers() });
  return res.json();
}

export async function fetchBrief(type: "morning" | "eod" | "next-day" | "reminders"): Promise<string> {
  const res = await fetch(`${API_BASE}/brief/${type}`, { headers: headers() });
  const data = await res.json();
  return data.brief;
}

export async function* streamChat(
  message: string,
  sessionId: string
): AsyncGenerator<{ type: string; content?: string; response?: string }> {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      message,
      session_id: sessionId,
      input_channel: "text",
      output_channel: "text",
    }),
  });
  if (!res.ok || !res.body) throw new Error(`Chat stream failed: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        yield JSON.parse(line.slice(6));
      }
    }
  }
}

export async function voiceChat(
  transcript: string,
  sessionId: string
): Promise<ChatEnvelope> {
  const res = await fetch(`${API_BASE}/voice/chat`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      transcript,
      session_id: sessionId,
      input_channel: "voice",
      output_channel: "voice",
    }),
  });
  if (!res.ok) throw new Error(`Voice chat failed: ${res.status}`);
  return res.json();
}

export async function transcribeAudio(
  audioBase64: string,
  mimeType: string,
  browserTranscript?: string
): Promise<string> {
  const res = await fetch(`${API_BASE}/voice/stt/transcribe`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      audio_base64: audioBase64,
      mime_type: mimeType,
      browser_transcript: browserTranscript ?? "",
    }),
  });
  const data = await res.json();
  return data.text || browserTranscript || "";
}

export async function clearSession(sessionId: string): Promise<void> {
  await fetch(`${API_BASE}/chat/${sessionId}`, {
    method: "DELETE",
    headers: headers(),
  });
}

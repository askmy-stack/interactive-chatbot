/**
 * A.S.K. TypeScript SDK — minimal client for external integrations.
 */

export type AskClientType = "standalone-web" | "external-app" | "cli";
export type InputChannel = "text" | "voice";
export type OutputChannel = "text" | "voice";

export interface AskConfig {
  baseUrl?: string;
  apiKey?: string;
  client?: AskClientType;
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

export interface StreamEvent {
  type: "meta" | "token" | "done";
  session_id?: string;
  input_channel?: InputChannel;
  output_channel?: OutputChannel;
  content?: string;
  response?: string;
}

export class AskClient {
  private baseUrl: string;
  private apiKey?: string;
  private client: AskClientType;

  constructor(config: AskConfig = {}) {
    this.baseUrl = (config.baseUrl ?? "http://localhost:8000").replace(/\/$/, "");
    this.apiKey = config.apiKey;
    this.client = config.client ?? "external-app";
  }

  private headers(): Record<string, string> {
    const h: Record<string, string> = {
      "Content-Type": "application/json",
      "X-ASK-Client": this.client,
    };
    if (this.apiKey) {
      h["Authorization"] = `Bearer ${this.apiKey}`;
    }
    return h;
  }

  async health(): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/health`, { headers: this.headers() });
    return res.json();
  }

  async chat(message: string, sessionId = "default"): Promise<ChatEnvelope> {
    const res = await fetch(`${this.baseUrl}/chat`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({
        message,
        session_id: sessionId,
        input_channel: "text",
        output_channel: "text",
      }),
    });
    if (!res.ok) throw new Error(`chat failed: ${res.status}`);
    return res.json();
  }

  async *chatStream(
    message: string,
    sessionId = "default"
  ): AsyncGenerator<StreamEvent> {
    const res = await fetch(`${this.baseUrl}/chat/stream`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({
        message,
        session_id: sessionId,
        input_channel: "text",
        output_channel: "text",
      }),
    });
    if (!res.ok || !res.body) throw new Error(`stream failed: ${res.status}`);

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
          yield JSON.parse(line.slice(6)) as StreamEvent;
        }
      }
    }
  }

  async voiceChat(transcript: string, sessionId = "default"): Promise<ChatEnvelope> {
    const res = await fetch(`${this.baseUrl}/voice/chat`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({
        transcript,
        session_id: sessionId,
        input_channel: "voice",
        output_channel: "voice",
      }),
    });
    if (!res.ok) throw new Error(`voice chat failed: ${res.status}`);
    return res.json();
  }

  async morningBrief(): Promise<string> {
    const res = await fetch(`${this.baseUrl}/brief/morning`, { headers: this.headers() });
    const data = await res.json();
    return data.brief;
  }

  async eodBrief(): Promise<string> {
    const res = await fetch(`${this.baseUrl}/brief/eod`, { headers: this.headers() });
    const data = await res.json();
    return data.brief;
  }

  async calendarApprove(action: "create_event" | "update_event"): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/calendar/approve`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({ action }),
    });
    return res.json();
  }

  async clearSession(sessionId: string): Promise<void> {
    await fetch(`${this.baseUrl}/chat/${sessionId}`, {
      method: "DELETE",
      headers: this.headers(),
    });
  }
}

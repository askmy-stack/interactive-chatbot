"use client";

import type { TimelineMessage } from "@/lib/ask-client";

interface Props {
  messages: TimelineMessage[];
  streamingContent?: string;
}

export default function ChatTimeline({ messages, streamingContent }: Props) {
  return (
    <div style={{ flex: 1, overflowY: "auto", padding: "1rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {messages.length === 0 && !streamingContent && (
        <p style={{ color: "var(--muted)", textAlign: "center", marginTop: "2rem" }}>
          Ask me anything — type a message or hold the mic button to speak.
        </p>
      )}
      {messages.map((msg) => (
        <div
          key={msg.id}
          style={{
            alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
            maxWidth: "80%",
            padding: "0.75rem 1rem",
            borderRadius: "12px",
            background: msg.role === "user" ? "var(--user-bg)" : "var(--ai-bg)",
            border: "1px solid var(--border)",
          }}
        >
          <div style={{ fontSize: "0.7rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
            {msg.role === "user" ? "You" : "A.S.K."} · {msg.channel}
          </div>
          <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{msg.content}</div>
        </div>
      ))}
      {streamingContent && (
        <div
          style={{
            alignSelf: "flex-start",
            maxWidth: "80%",
            padding: "0.75rem 1rem",
            borderRadius: "12px",
            background: "var(--ai-bg)",
            border: "1px solid var(--border)",
          }}
        >
          <div style={{ fontSize: "0.7rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
            A.S.K. · text
          </div>
          <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{streamingContent}</div>
        </div>
      )}
    </div>
  );
}

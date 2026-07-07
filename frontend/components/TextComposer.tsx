"use client";

import { useState, KeyboardEvent } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function TextComposer({ onSend, disabled }: Props) {
  const [text, setText] = useState("");

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: "flex", gap: "0.5rem", padding: "0.75rem", borderTop: "1px solid var(--border)" }}>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a message..."
        disabled={disabled}
        rows={1}
        style={{
          flex: 1,
          resize: "none",
          padding: "0.6rem 0.8rem",
          borderRadius: "8px",
          border: "1px solid var(--border)",
          background: "var(--surface)",
          color: "var(--text)",
          fontSize: "0.95rem",
        }}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !text.trim()}
        style={{
          padding: "0.6rem 1.2rem",
          borderRadius: "8px",
          border: "none",
          background: "var(--accent)",
          color: "#fff",
          fontWeight: 600,
          opacity: disabled || !text.trim() ? 0.5 : 1,
        }}
      >
        Send
      </button>
    </div>
  );
}

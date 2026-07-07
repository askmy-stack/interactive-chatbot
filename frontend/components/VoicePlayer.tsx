"use client";

interface Props {
  isSpeaking: boolean;
  onStop: () => void;
  ttsUnavailable?: string | null;
}

export default function VoicePlayer({ isSpeaking, onStop, ttsUnavailable }: Props) {
  if (ttsUnavailable) {
    return (
      <div style={{ padding: "0.5rem 0.75rem", fontSize: "0.8rem", color: "var(--danger)", borderTop: "1px solid var(--border)" }}>
        TTS unavailable: {ttsUnavailable}
      </div>
    );
  }

  if (!isSpeaking) return null;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 0.75rem", borderTop: "1px solid var(--border)" }}>
      <span style={{ fontSize: "0.85rem", color: "var(--success)" }}>Speaking…</span>
      <button
        onClick={onStop}
        style={{
          padding: "0.3rem 0.8rem",
          borderRadius: "6px",
          border: "1px solid var(--danger)",
          background: "transparent",
          color: "var(--danger)",
          fontSize: "0.8rem",
        }}
      >
        Stop
      </button>
    </div>
  );
}

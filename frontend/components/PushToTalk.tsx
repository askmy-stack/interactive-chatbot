"use client";

interface Props {
  isListening: boolean;
  isProcessing: boolean;
  onStart: () => void;
  onStop: () => void;
  disabled?: boolean;
}

export default function PushToTalk({ isListening, isProcessing, onStart, onStop, disabled }: Props) {
  return (
    <button
      onMouseDown={onStart}
      onMouseUp={onStop}
      onMouseLeave={isListening ? onStop : undefined}
      onTouchStart={(e) => { e.preventDefault(); onStart(); }}
      onTouchEnd={(e) => { e.preventDefault(); onStop(); }}
      disabled={disabled || isProcessing}
      style={{
        width: "48px",
        height: "48px",
        borderRadius: "50%",
        border: "none",
        background: isListening ? "var(--danger)" : isProcessing ? "var(--muted)" : "var(--accent)",
        color: "#fff",
        fontSize: "1.2rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        opacity: disabled ? 0.4 : 1,
        transition: "background 0.15s",
      }}
      title={isListening ? "Release to send" : "Hold to talk"}
    >
      {isProcessing ? "…" : isListening ? "●" : "🎤"}
    </button>
  );
}

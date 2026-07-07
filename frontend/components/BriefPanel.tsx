"use client";

interface Props {
  brief: string;
  loading?: boolean;
  onRefresh?: () => void;
}

export default function BriefPanel({ brief, loading, onRefresh }: Props) {
  return (
    <div
      style={{
        width: "280px",
        borderLeft: "1px solid var(--border)",
        padding: "1rem",
        overflowY: "auto",
        background: "var(--surface)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
        <h3 style={{ fontSize: "0.9rem", fontWeight: 600 }}>Morning Brief</h3>
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={loading}
            style={{
              padding: "0.25rem 0.5rem",
              fontSize: "0.75rem",
              borderRadius: "4px",
              border: "1px solid var(--border)",
              background: "transparent",
              color: "var(--muted)",
            }}
          >
            {loading ? "…" : "Refresh"}
          </button>
        )}
      </div>
      <div style={{ fontSize: "0.85rem", lineHeight: 1.6, color: "var(--muted)", whiteSpace: "pre-wrap" }}>
        {loading ? "Loading brief…" : brief || "No brief available."}
      </div>
    </div>
  );
}

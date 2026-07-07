"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchHealth, clearSession, type HealthInfo } from "@/lib/ask-client";

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [cleared, setCleared] = useState(false);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => {});
  }, []);

  const handleClearSession = async () => {
    await clearSession("web-default");
    setCleared(true);
    setTimeout(() => setCleared(false), 2000);
  };

  return (
    <div style={{ maxWidth: "600px", margin: "2rem auto", padding: "0 1rem" }}>
      <Link href="/" style={{ fontSize: "0.85rem" }}>
        ← Back to chat
      </Link>
      <h1 style={{ fontSize: "1.5rem", margin: "1rem 0" }}>Settings</h1>

      <section style={{ marginBottom: "2rem" }}>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Provider</h2>
        {health ? (
          <div style={{ fontSize: "0.9rem", color: "var(--muted)", lineHeight: 1.8 }}>
            <div>Provider: {health.provider}</div>
            <div>Model: {health.model}</div>
            <div>Deployment: {health.deployment_mode}</div>
            <div>
              TTS:{" "}
              {health.tts?.tts_available
                ? `available (${health.tts.providers?.join(", ")})`
                : "unavailable"}
            </div>
          </div>
        ) : (
          <p style={{ color: "var(--muted)" }}>Loading…</p>
        )}
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Privacy</h2>
        <p style={{ fontSize: "0.85rem", color: "var(--muted)", lineHeight: 1.6 }}>
          A.S.K. runs locally by default with Ollama. No data leaves your machine unless you
          configure a cloud provider. Set environment variables in <code>.env</code> to change
          provider, API keys, and privacy mode.
        </p>
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Session</h2>
        <button
          onClick={handleClearSession}
          style={{
            padding: "0.5rem 1rem",
            borderRadius: "6px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            color: "var(--text)",
            fontSize: "0.85rem",
          }}
        >
          {cleared ? "Cleared!" : "Clear chat history"}
        </button>
      </section>

      <section>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Integration</h2>
        <p style={{ fontSize: "0.85rem", color: "var(--muted)", lineHeight: 1.6 }}>
          For sidecar or embedded mode, see{" "}
          <code>docs/integration-guide.md</code> and the SDKs in <code>sdk/</code>.
        </p>
      </section>
    </div>
  );
}

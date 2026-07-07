"use client";

import { useCallback, useEffect, useState } from "react";
import ChatTimeline from "@/components/ChatTimeline";
import TextComposer from "@/components/TextComposer";
import PushToTalk from "@/components/PushToTalk";
import VoicePlayer from "@/components/VoicePlayer";
import BriefPanel from "@/components/BriefPanel";
import {
  fetchHealth,
  fetchBrief,
  transcribeAudio,
  type TimelineMessage,
  type HealthInfo,
} from "@/lib/ask-client";
import { sendTextMessage, sendVoiceMessage, stopAudio } from "@/lib/channel-router";
import { startRecording, stopRecording } from "@/lib/audio";
import Link from "next/link";

const SESSION_ID = "web-default";

export default function HomePage() {
  const [messages, setMessages] = useState<TimelineMessage[]>([]);
  const [streaming, setStreaming] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [ttsUnavailable, setTtsUnavailable] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [brief, setBrief] = useState("");
  const [briefLoading, setBriefLoading] = useState(false);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => {});
    loadBrief();
  }, []);

  const loadBrief = useCallback(async () => {
    setBriefLoading(true);
    try {
      const b = await fetchBrief("morning");
      setBrief(b);
    } catch {
      setBrief("Could not load brief.");
    } finally {
      setBriefLoading(false);
    }
  }, []);

  const handleTextSend = async (text: string) => {
    setBusy(true);
    setStreaming("");
    try {
      const result = await sendTextMessage(text, SESSION_ID, (token) => {
        setStreaming((prev) => prev + token);
      });
      setMessages((prev) => [...prev, result.userMessage, result.assistantMessage]);
      setStreaming("");
    } catch (err) {
      console.error(err);
    } finally {
      setBusy(false);
    }
  };

  const handleVoiceStart = async () => {
    try {
      await startRecording();
      setListening(true);
      setTtsUnavailable(null);
    } catch {
      setTtsUnavailable("Microphone access denied");
    }
  };

  const handleVoiceStop = async () => {
    if (!listening) return;
    setListening(false);
    setProcessing(true);
    try {
      const { base64, mimeType } = await stopRecording();
      const transcript = await transcribeAudio(base64, mimeType);
      if (!transcript.trim()) {
        setTtsUnavailable("No speech detected");
        return;
      }
      setSpeaking(true);
      const result = await sendVoiceMessage(transcript, SESSION_ID);
      setMessages((prev) => [...prev, result.userMessage, result.assistantMessage]);
      if (result.ttsUnavailable) {
        setTtsUnavailable(result.ttsUnavailable);
      }
    } catch (err) {
      console.error(err);
      setTtsUnavailable("Voice processing failed");
    } finally {
      setProcessing(false);
      setSpeaking(false);
    }
  };

  const handleStopSpeaking = () => {
    stopAudio();
    setSpeaking(false);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "0.75rem 1rem",
          borderBottom: "1px solid var(--border)",
          background: "var(--surface)",
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.1rem", fontWeight: 700 }}>A.S.K.</h1>
          {health && (
            <span style={{ fontSize: "0.75rem", color: "var(--muted)" }}>
              {health.provider} · {health.model}
              {health.tts?.tts_available ? "" : " · TTS off"}
            </span>
          )}
        </div>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          {listening && (
            <span style={{ fontSize: "0.85rem", color: "var(--danger)", fontWeight: 600 }}>
              Listening…
            </span>
          )}
          <Link href="/settings" style={{ fontSize: "0.85rem" }}>
            Settings
          </Link>
        </div>
      </header>

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          <ChatTimeline messages={messages} streamingContent={streaming} />
          <VoicePlayer
            isSpeaking={speaking}
            onStop={handleStopSpeaking}
            ttsUnavailable={ttsUnavailable}
          />
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0 0.75rem 0.75rem",
            }}
          >
            <PushToTalk
              isListening={listening}
              isProcessing={processing}
              onStart={handleVoiceStart}
              onStop={handleVoiceStop}
              disabled={busy}
            />
            <div style={{ flex: 1 }}>
              <TextComposer onSend={handleTextSend} disabled={busy || listening} />
            </div>
          </div>
        </div>
        <BriefPanel brief={brief} loading={briefLoading} onRefresh={loadBrief} />
      </div>
    </div>
  );
}

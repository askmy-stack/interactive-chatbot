"""
A.S.K. — Streamlit frontend.

Connects to the FastAPI backend (default: http://localhost:8000) and streams
responses token-by-token so the user sees text appearing in real time.

Start the backend first:
    uvicorn backend.main:app --reload

Then run this UI:
    streamlit run app.py
"""

import base64
import os
import uuid

import requests
import streamlit as st
from dotenv import load_dotenv

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="A.S.K.",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def _append_timeline(role: str, content: str, *, channel: str = "text") -> None:
    st.session_state.timeline.append(
        {"role": role, "content": content, "channel": channel}
    )


def _sync_messages_from_timeline() -> None:
    st.session_state.messages = [
        {"role": item["role"], "content": item["content"]}
        for item in st.session_state.timeline
    ]


# ── Session state bootstrap ───────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "timeline" not in st.session_state:
    st.session_state.timeline = []

if "messages" not in st.session_state:
    st.session_state.messages = []


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ A.S.K.")
    st.caption("Autonomous System Kernel")
    st.caption(f"Session: `{st.session_state.session_id[:8]}...`")

    st.divider()
    st.markdown("**Capabilities**")
    st.markdown(
        "- 🔍 Web search (DuckDuckGo)\n"
        "- 🌤️ Live weather (Open-Meteo)\n"
        "- 💻 System resource monitor\n"
        "- 🏠 Smart home control (Home Assistant)\n"
        "- 🎙️ Push-to-talk voice (STT + TTS)\n"
        "- 📅 Calendar read/write (approval required)\n"
        "- 🧠 Persistent vector + graph memory"
    )

    st.divider()
    st.markdown("**Workflow briefs**")
    col_a, col_b = st.columns(2)
    brief_routes = {
        "Morning": "/brief/morning",
        "EOD": "/brief/eod",
        "Next day": "/brief/next-day",
        "Reminders": "/brief/reminders",
    }
    for idx, (label, route) in enumerate(brief_routes.items()):
        target = col_a if idx % 2 == 0 else col_b
        with target:
            if st.button(label, use_container_width=True, key=f"brief_{label}"):
                try:
                    brief_resp = requests.get(f"{BACKEND_URL}{route}", timeout=8).json()
                    text = brief_resp.get("brief", "No brief available.")
                    _append_timeline("assistant", text, channel="brief")
                    _sync_messages_from_timeline()
                    st.rerun()
                except Exception:
                    st.warning(f"Could not fetch {label.lower()} brief.")

    st.divider()
    if st.button("🗑️ Clear conversation", use_container_width=True):
        try:
            requests.delete(f"{BACKEND_URL}/chat/{st.session_state.session_id}", timeout=3)
        except Exception:
            pass
        st.session_state.timeline = []
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.divider()
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=2).json()
        provider = health.get("provider", "?")
        model = health.get("model", "?")
        st.success(f"Backend online · {provider} / {model}")
        stt = requests.get(f"{BACKEND_URL}/voice/stt/status", timeout=2).json()
        backends = ", ".join(stt.get("backends", []))
        st.caption(f"STT backends: {backends}")
    except Exception:
        st.error("Backend offline — start it with:\n`uvicorn backend.main:app`")


# ── Main chat area ─────────────────────────────────────────────────────────────
st.title("🤖 A.S.K. — Autonomous System Kernel")
st.caption("Unified voice + text session timeline with push-to-talk.")

st.subheader("🎙️ Push-to-talk")
stt_status = {}
try:
    stt_status = requests.get(f"{BACKEND_URL}/voice/stt/status", timeout=2).json()
except Exception:
    stt_status = {"backends": ["browser_transcript"], "local_stt_available": False}

if not stt_status.get("local_stt_available"):
    st.info(
        "Local STT unavailable in this environment. "
        "Hold-to-talk still works via browser transcript fallback."
    )

audio_input = None
try:
    audio_input = st.audio_input("Hold to record, release to transcribe", key="ptt_audio")
except Exception:
    st.caption("Upgrade Streamlit to use native audio input, or use transcript fallback below.")

browser_transcript = st.text_input(
    "Browser transcript fallback",
    value="",
    key="voice_transcript",
    help="Used when local STT is unavailable (CI/Linux) or as validation fallback.",
)

ptt_col1, ptt_col2 = st.columns([1, 3])
with ptt_col1:
    send_voice = st.button("🎤 Send voice", use_container_width=True)
with ptt_col2:
    st.caption("Voice turns appear in the same timeline as text chat.")

if send_voice:
    transcript = browser_transcript.strip()
    stt_backend = "browser_transcript"

    if audio_input is not None:
        try:
            audio_bytes = audio_input.getvalue()
            if audio_bytes:
                payload = {
                    "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
                    "mime_type": "audio/wav",
                    "browser_transcript": browser_transcript,
                }
                tr = requests.post(
                    f"{BACKEND_URL}/voice/stt/transcribe", json=payload, timeout=30
                ).json()
                if tr.get("text"):
                    transcript = tr["text"]
                    stt_backend = tr.get("backend", "unknown")
        except Exception as exc:
            st.warning(f"STT failed, using transcript fallback: {exc}")

    if transcript:
        try:
            payload = {"transcript": transcript, "session_id": st.session_state.session_id}
            vr = requests.post(f"{BACKEND_URL}/voice/chat", json=payload, timeout=60).json()
            _append_timeline(
                "user",
                f"[voice/{stt_backend}] {vr.get('transcript', transcript)}",
                channel="voice",
            )
            _append_timeline("assistant", vr.get("response", ""), channel="voice")
            _sync_messages_from_timeline()
            st.rerun()
        except Exception as exc:
            st.error(f"Voice request failed: {exc}")
    else:
        st.warning("No transcript captured. Type a fallback transcript or record audio.")

st.divider()
st.subheader("💬 Conversation timeline")

for item in st.session_state.timeline:
    role = item["role"]
    channel = item.get("channel", "text")
    icon = "🎙️" if channel == "voice" else ("📋" if channel == "brief" else None)
    label = f"{icon} {role}" if icon else role
    with st.chat_message(role):
        if icon:
            st.caption(channel)
        st.markdown(item["content"])

user_input = st.chat_input("Ask A.S.K. anything…", key="chat_input")

if user_input:
    _append_timeline("user", user_input, channel="text")
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        try:
            with requests.post(
                f"{BACKEND_URL}/chat/stream",
                json={"message": user_input, "session_id": st.session_state.session_id},
                stream=True,
                timeout=60,
            ) as resp:
                resp.raise_for_status()
                for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        full_response += chunk
                        placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

        except requests.exceptions.ConnectionError:
            full_response = (
                "**Cannot reach the A.S.K. backend.**\n\n"
                "Start it with:\n```\nuvicorn backend.main:app --reload\n```"
            )
            placeholder.error(full_response)

        except requests.exceptions.Timeout:
            full_response = "The request timed out. The model may be taking too long — try again."
            placeholder.warning(full_response)

        except Exception as exc:
            full_response = f"Unexpected error: {exc}"
            placeholder.error(full_response)

    _append_timeline("assistant", full_response, channel="text")
    _sync_messages_from_timeline()

"""
A.S.K. — Streamlit frontend.

Connects to the FastAPI backend (default: http://localhost:8000) and streams
responses token-by-token so the user sees text appearing in real time.

Start the backend first:
    uvicorn backend.main:app --reload

Then run this UI:
    streamlit run app.py
"""

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

# ── Read backend URL from environment (falls back to localhost) ────────────────
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── Session state bootstrap ───────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []  # [{role, content}, ...]


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
        "- 🧠 Persistent vector memory"
    )

    st.divider()
    st.markdown("**Example prompts**")
    examples = [
        "What's my CPU usage right now?",
        "What is my calendar today?",
        "What's the weather in Tokyo?",
        "Search for the latest news on AI agents",
        "Turn off the bedroom lights",
        "Who won the last Formula 1 race?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.prefill = ex

    st.divider()
    if st.button("🗑️ Clear conversation", use_container_width=True):
        try:
            requests.delete(f"{BACKEND_URL}/chat/{st.session_state.session_id}", timeout=3)
        except Exception:
            pass
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    if st.button("🗓️ Morning brief", use_container_width=True):
        try:
            brief_resp = requests.get(f"{BACKEND_URL}/brief/morning", timeout=5).json()
            st.session_state.messages.append({"role": "assistant", "content": brief_resp.get("brief", "No brief available.")})
            st.rerun()
        except Exception:
            st.warning("Could not fetch morning brief.")

    # Backend health indicator
    st.divider()
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=2).json()
        provider = health.get("provider", "?")
        model = health.get("model", "?")
        st.success(f"Backend online · {provider} / {model}")
    except Exception:
        st.error("Backend offline — start it with:\n`uvicorn backend.main:app`")


# ── Main chat area ─────────────────────────────────────────────────────────────
st.title("🤖 A.S.K. — Autonomous System Kernel")
st.caption("Your personal assistant with real-time tools and persistent memory.")

voice_transcript = st.text_input("Voice transcript (fallback input)", value="", key="voice_transcript")
if st.button("🎤 Send voice transcript", use_container_width=False) and voice_transcript.strip():
    try:
        payload = {"transcript": voice_transcript, "session_id": st.session_state.session_id}
        vr = requests.post(f"{BACKEND_URL}/voice/chat", json=payload, timeout=60).json()
        st.session_state.messages.append({"role": "user", "content": f"[voice] {vr.get('transcript', voice_transcript)}"})
        st.session_state.messages.append({"role": "assistant", "content": vr.get("response", "")})
        st.rerun()
    except Exception as exc:
        st.error(f"Voice request failed: {exc}")

# Render existing conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle sidebar example button pre-fill
prefill = st.session_state.pop("prefill", None)

# Chat input
user_input = st.chat_input("Ask A.S.K. anything…", key="chat_input")
if prefill and not user_input:
    user_input = prefill

if user_input:
    # Render user bubble immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Stream assistant response
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

    st.session_state.messages.append({"role": "assistant", "content": full_response})

"""
A.S.K. LangChain tool-calling agent.

Uses the configured LLM provider (Ollama by default) with tools:
  - get_system_info  — host CPU/memory/disk
  - web_search       — DuckDuckGo (no key needed)
  - get_weather      — Open-Meteo (no key needed)
  - control_device   — Home Assistant (requires .env config)

Streaming is implemented via AgentExecutor.astream_events (v2), which yields
individual LLM tokens as they arrive and announces tool calls in real time.
"""

from __future__ import annotations

import structlog
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from backend.memory import retrieve_memories, save_to_memory
from backend.providers import get_chat_model
from backend.tools.calendar_apple import get_free_time_blocks, get_next_event, get_today_schedule
from backend.tools.device_control import control_device
from backend.tools.system_info import get_system_info
from backend.tools.weather import get_weather
from backend.tools.web_search import web_search

log = structlog.get_logger()

TOOLS = [
    get_system_info,
    web_search,
    get_weather,
    control_device,
    get_today_schedule,
    get_next_event,
    get_free_time_blocks,
]

SYSTEM_PROMPT = """\
You are Jarvis, a highly capable personal AI assistant. You have access to these tools:

• get_system_info   — check host CPU, memory, and disk usage
• web_search        — search the web for current information
• get_weather       — get live weather for any city worldwide
• control_device    — control smart home devices via Home Assistant
• get_today_schedule — read today's Apple Calendar events
• get_next_event    — get your next scheduled calendar event
• get_free_time_blocks — get open windows in today's calendar

Behaviour rules:
- Be concise and action-oriented. Confirm every action you take.
- Always use a tool when the question involves real-time data (weather, search, system stats).
- For device control, confirm what you did and whether it succeeded.
- If Home Assistant is not configured, acknowledge it clearly.
- When in doubt, ask a clarifying question before acting.

{memory_context}"""


def _build_agent() -> AgentExecutor:
    llm = get_chat_model(streaming=True)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=TOOLS, verbose=True, max_iterations=6)


# Lazy singleton — not initialised until first request so imports are test-safe
_executor: AgentExecutor | None = None


def get_executor() -> AgentExecutor:
    global _executor
    if _executor is None:
        _executor = _build_agent()
    return _executor


async def astream_response(
    user_input: str,
    session_id: str,
    chat_history: list[BaseMessage],
):
    """
    Async generator that yields text chunks as they arrive from the LLM.

    Yields:
      - Individual LLM tokens (streamed character-by-character feel)
      - Italic tool-use announcements so the user can see Jarvis thinking
    """
    memories = retrieve_memories(user_input)
    memory_context = memories if memories else ""

    executor = get_executor()
    full_response = ""

    log.info("agent_stream_start", session_id=session_id, input_preview=user_input[:80])

    async for event in executor.astream_events(
        {
            "input": user_input,
            "chat_history": chat_history,
            "memory_context": memory_context,
        },
        version="v2",
    ):
        kind = event["event"]

        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            content = getattr(chunk, "content", "")
            if content:
                full_response += content
                yield content

        elif kind == "on_tool_start":
            tool_name = event.get("name", "tool")
            announcement = f"\n\n*Using **{tool_name}**...*\n\n"
            yield announcement

    log.info("agent_stream_done", session_id=session_id, response_len=len(full_response))

    # Persist exchange to long-term vector memory (non-blocking — errors are swallowed)
    try:
        save_to_memory(session_id, user_input, full_response)
    except Exception as exc:
        log.warning("memory_save_failed", error=str(exc))

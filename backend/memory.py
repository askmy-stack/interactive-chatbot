"""
Long-term vector memory backed by ChromaDB.

Each conversation turn is embedded and stored on disk in ./chroma_db.
On every new query the top-k semantically similar past exchanges are retrieved
and injected into the agent's context — giving Jarvis memory across sessions.
"""

from __future__ import annotations

import structlog
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

log = structlog.get_logger()

_vectorstore: Chroma | None = None


def _get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        _vectorstore = Chroma(
            collection_name="jarvis_memory",
            embedding_function=embeddings,
            persist_directory="./chroma_db",
        )
        log.info("vectorstore_initialized", persist_directory="./chroma_db")
    return _vectorstore


def save_to_memory(session_id: str, human: str, assistant: str) -> None:
    """Embed and persist a conversation turn."""
    vs = _get_vectorstore()
    vs.add_texts(
        texts=[f"User: {human}\nJarvis: {assistant}"],
        metadatas=[{"session_id": session_id}],
    )
    log.info("memory_saved", session_id=session_id)


def retrieve_memories(query: str, k: int = 3) -> str:
    """Return relevant past exchanges as a formatted string, or empty string if none."""
    vs = _get_vectorstore()
    try:
        docs = vs.similarity_search(query, k=k)
    except Exception:
        return ""

    if not docs:
        return ""

    excerpts = "\n---\n".join(doc.page_content for doc in docs)
    return f"Relevant past context (from memory):\n{excerpts}"

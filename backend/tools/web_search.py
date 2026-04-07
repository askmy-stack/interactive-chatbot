"""Tool: web search via DuckDuckGo (no API key required)."""

import structlog
from duckduckgo_search import DDGS
from langchain_core.tools import tool

log = structlog.get_logger()


@tool
def web_search(query: str) -> str:
    """
    Search the web for up-to-date information using DuckDuckGo.
    Use this for current events, facts you are unsure about, or anything
    requiring real-time data. Returns the top 3 results.
    """
    log.info("web_search", query=query)
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
    except Exception as exc:
        return f"Search failed: {exc}"

    if not results:
        return "No results found for that query."

    formatted = []
    for r in results:
        formatted.append(f"**{r['title']}**\n{r['body']}\nSource: {r['href']}")

    return "\n\n".join(formatted)

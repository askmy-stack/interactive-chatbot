"""
Tool: smart home device control via Home Assistant REST API.

Requires HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN in .env.
All device domains and actions are validated against strict allow-lists
so the LLM cannot be used to execute arbitrary API calls.
"""

import requests
import structlog
from langchain_core.tools import tool

log = structlog.get_logger()

# Security: LLM can only target these entity domains
ALLOWED_DOMAINS: frozenset[str] = frozenset(
    {"light", "switch", "fan", "media_player", "climate", "cover"}
)

# Security: LLM can only invoke these HA service actions
ALLOWED_ACTIONS: frozenset[str] = frozenset({"turn_on", "turn_off", "toggle"})


@tool
def control_device(entity_id: str, action: str) -> str:
    """
    Control a smart home device via Home Assistant.

    entity_id: Home Assistant entity ID, e.g. 'light.bedroom', 'switch.fan',
               'media_player.living_room', 'climate.thermostat'.
    action: One of 'turn_on', 'turn_off', 'toggle'.

    Requires HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN to be set in .env.
    Returns a confirmation string or an error message.
    """
    # Read settings at call time so tests can patch env vars cleanly
    from backend.config import settings

    if not settings.home_assistant_url or not settings.home_assistant_token:
        return (
            "Home Assistant is not configured. "
            "Set HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN in your .env file."
        )

    # Allow-list validation — never trust LLM-supplied strings directly
    parts = entity_id.split(".", 1)
    if len(parts) != 2:
        return f"Invalid entity_id format '{entity_id}'. Expected 'domain.name', e.g. 'light.bedroom'."

    domain = parts[0]
    if domain not in ALLOWED_DOMAINS:
        return (
            f"Device domain '{domain}' is not allowed. "
            f"Allowed domains: {sorted(ALLOWED_DOMAINS)}"
        )

    if action not in ALLOWED_ACTIONS:
        return (
            f"Action '{action}' is not allowed. "
            f"Allowed actions: {sorted(ALLOWED_ACTIONS)}"
        )

    url = f"{settings.home_assistant_url}/api/services/{domain}/{action}"
    headers = {
        "Authorization": f"Bearer {settings.home_assistant_token}",
        "Content-Type": "application/json",
    }

    log.info("device_control", entity_id=entity_id, action=action)

    try:
        resp = requests.post(url, json={"entity_id": entity_id}, headers=headers, timeout=5)
    except requests.exceptions.ConnectionError:
        return f"Cannot reach Home Assistant at {settings.home_assistant_url}. Is it running?"
    except requests.exceptions.Timeout:
        return "Home Assistant request timed out."

    if resp.ok:
        return f"Done: {entity_id} → {action}"
    return f"Home Assistant error {resp.status_code}: {resp.text}"

"""
Unit tests for the Jarvis tool functions.

These tests do NOT call OpenAI or any external LLM.
They cover input validation, allow-list enforcement, and real system calls.
"""



# ── system_info ────────────────────────────────────────────────────────────────

def test_system_info_returns_expected_fields():
    from backend.tools.system_info import get_system_info

    result = get_system_info.invoke({})
    assert "CPU" in result
    assert "Memory" in result
    assert "Disk" in result
    assert "%" in result


# ── device_control — no Home Assistant configured ─────────────────────────────

def test_device_control_no_ha_config(monkeypatch):
    """Without HA env vars, the tool should return a friendly config message."""
    monkeypatch.delenv("HOME_ASSISTANT_URL", raising=False)
    monkeypatch.delenv("HOME_ASSISTANT_TOKEN", raising=False)

    # Reload config so the monkeypatch takes effect
    import importlib

    import backend.config
    importlib.reload(backend.config)

    from backend.tools.device_control import control_device

    result = control_device.invoke({"entity_id": "light.bedroom", "action": "turn_on"})
    assert "not configured" in result.lower()


# ── device_control — allow-list enforcement ───────────────────────────────────

def test_device_control_blocks_invalid_domain(monkeypatch):
    monkeypatch.setenv("HOME_ASSISTANT_URL", "http://ha.local:8123")
    monkeypatch.setenv("HOME_ASSISTANT_TOKEN", "fake-token")

    import importlib

    import backend.config
    importlib.reload(backend.config)

    from backend.tools.device_control import control_device

    result = control_device.invoke({"entity_id": "shell.dangerous", "action": "turn_on"})
    assert "not allowed" in result


def test_device_control_blocks_invalid_action(monkeypatch):
    monkeypatch.setenv("HOME_ASSISTANT_URL", "http://ha.local:8123")
    monkeypatch.setenv("HOME_ASSISTANT_TOKEN", "fake-token")

    import importlib

    import backend.config
    importlib.reload(backend.config)

    from backend.tools.device_control import control_device

    result = control_device.invoke({"entity_id": "light.bedroom", "action": "rm -rf /"})
    assert "not allowed" in result


def test_device_control_rejects_malformed_entity_id(monkeypatch):
    monkeypatch.setenv("HOME_ASSISTANT_URL", "http://ha.local:8123")
    monkeypatch.setenv("HOME_ASSISTANT_TOKEN", "fake-token")

    import importlib

    import backend.config
    importlib.reload(backend.config)

    from backend.tools.device_control import control_device

    result = control_device.invoke({"entity_id": "no-dot-here", "action": "turn_on"})
    assert "invalid" in result.lower()


# ── weather ────────────────────────────────────────────────────────────────────

def test_weather_unknown_city():
    from backend.tools.weather import get_weather

    result = get_weather.invoke({"city": "xyzzyinvalidcity12345"})
    assert "could not find" in result.lower() or "no results" in result.lower() or "not find" in result.lower()


# ── web_search ─────────────────────────────────────────────────────────────────

def test_web_search_returns_results():
    from backend.tools.web_search import web_search

    result = web_search.invoke({"query": "Python programming language"})
    # Should return content or a graceful error — never raise
    assert isinstance(result, str)
    assert len(result) > 0

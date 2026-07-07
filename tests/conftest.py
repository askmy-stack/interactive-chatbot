"""
Shared pytest fixtures.

Sets a fake OPENAI_API_KEY so pydantic-settings validation passes
without a real key during CI runs.
"""

import pytest


@pytest.fixture(autouse=True)
def fake_openai_key(monkeypatch):
    """Inject a placeholder API key so Settings() doesn't raise on import."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-placeholder-for-ci")

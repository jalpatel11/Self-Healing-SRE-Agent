"""Tests for config.py — Pydantic Settings validation."""
import importlib
import pytest


def _fresh_settings(monkeypatch, **env_overrides):
    """Helper: reload config module with patched env vars, return a fresh Settings()."""
    for key, value in env_overrides.items():
        monkeypatch.setenv(key, value)
    import config
    importlib.reload(config)
    from config import Settings
    return Settings()


def test_settings_load_with_groq(monkeypatch):
    """Settings loads correctly with Groq provider."""
    s = _fresh_settings(
        monkeypatch,
        LLM_PROVIDER="groq",
        GROQ_API_KEY="test-key-123",
    )
    assert s.llm_provider == "groq"
    assert s.groq_api_key == "test-key-123"
    assert s.max_iterations == 3


def test_settings_load_with_gemini(monkeypatch):
    """Settings loads correctly with Gemini provider."""
    s = _fresh_settings(
        monkeypatch,
        LLM_PROVIDER="gemini",
        GEMINI_API_KEY="gemini-key-abc",
    )
    assert s.llm_provider == "gemini"
    assert s.gemini_api_key == "gemini-key-abc"


def test_settings_missing_groq_key_raises(monkeypatch):
    """Empty GROQ_API_KEY raises ValueError when LLM_PROVIDER=groq.

    We set GROQ_API_KEY="" (empty string) which takes env-var priority
    over the .env file, so the validator sees a falsy value.
    """
    import config
    importlib.reload(config)
    from config import Settings
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "")
    with pytest.raises(Exception, match="GROQ_API_KEY"):
        Settings()


def test_settings_invalid_provider_raises(monkeypatch):
    """Unknown LLM_PROVIDER raises ValueError."""
    import config
    importlib.reload(config)
    from config import Settings
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("GROQ_API_KEY", "some-key")
    with pytest.raises(Exception, match="LLM_PROVIDER"):
        Settings()


def test_max_iterations_configurable(monkeypatch):
    """MAX_ITERATIONS env var overrides the default of 3."""
    s = _fresh_settings(
        monkeypatch,
        LLM_PROVIDER="groq",
        GROQ_API_KEY="test-key",
        MAX_ITERATIONS="5",
    )
    assert s.max_iterations == 5


def test_defaults(monkeypatch):
    """Default values are set correctly when not overridden."""
    s = _fresh_settings(
        monkeypatch,
        LLM_PROVIDER="groq",
        GROQ_API_KEY="test-key",
        LANGCHAIN_TRACING_V2="false",  # override .env which may have this set
    )
    assert s.app_port == 8000
    assert s.log_file == "app_logs.txt"
    assert s.github_branch == "main"
    assert s.langchain_tracing_v2 is False

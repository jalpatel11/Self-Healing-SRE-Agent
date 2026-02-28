"""Centralized configuration with startup validation.

All environment variables are defined here. Import `settings` anywhere in the
codebase instead of calling os.getenv() directly.

Usage:
    from config import settings
    llm_provider = settings.llm_provider
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    # ── LLM Provider ────────────────────────────────────────────
    llm_provider: str = "groq"  # "groq" | "gemini"

    # Groq (free at console.groq.com)
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"

    # Gemini (free at aistudio.google.com)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # ── GitHub ──────────────────────────────────────────────────
    github_token: str = ""
    github_repo: str = ""
    github_branch: str = "main"

    # ── Application ─────────────────────────────────────────────
    app_port: int = 8000
    log_file: str = "app_logs.txt"
    max_iterations: int = 3

    # ── LangSmith (optional) ────────────────────────────────────
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "sre-agent"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_llm_keys(self) -> "Settings":
        if self.llm_provider not in ("groq", "gemini"):
            raise ValueError(
                f"LLM_PROVIDER must be 'groq' or 'gemini', got: {self.llm_provider!r}"
            )
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is required when LLM_PROVIDER=groq. "
                "Get a free key at https://console.groq.com"
            )
        if self.llm_provider == "gemini" and not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when LLM_PROVIDER=gemini. "
                "Get a free key at https://aistudio.google.com"
            )
        return self


settings = Settings()

"""Tests for the sre-agent CLI entry point."""

import os
import subprocess
import sys


def test_cli_help():
    """sre-agent --help must exit 0 and mention 'heal'."""
    result = subprocess.run(
        [sys.executable, "-m", "sre_agent.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "heal" in result.stdout.lower()


def test_cli_missing_groq_key():
    """sre-agent heal must exit non-zero if GROQ_API_KEY is missing."""
    env = {k: v for k, v in os.environ.items() if k not in ("GROQ_API_KEY", "GEMINI_API_KEY")}
    result = subprocess.run(
        [sys.executable, "-m", "sre_agent.cli", "heal"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode != 0
    assert "GROQ_API_KEY" in result.stderr or "GEMINI_API_KEY" in result.stderr

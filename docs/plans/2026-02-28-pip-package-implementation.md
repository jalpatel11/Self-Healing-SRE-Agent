# pip Package Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure the Self-Healing SRE Agent into a distributable pip package (`self-healing-sre-agent`) with a `sre-agent heal` CLI so any Python repo can self-heal on CI failure by adding 1 secret and a 5-line workflow file.

**Architecture:** Move all agent code into a `sre_agent/` Python package, add a `pyproject.toml` build config, create a `cli.py` entry point, fix `fetch_logs` to call the real GitHub Actions API, and remove the hardcoded `file_path="app.py"` from `open_github_pr`. Demo files move to `demo/`. All tests updated to use new import paths.

**Tech Stack:** Python 3.10+, setuptools, pyproject.toml (PEP 517/518), httpx (GitHub API), LangGraph, LangChain-Groq, PyGithub, ruff, pytest

---

## Task 1: Create `sre_agent/` package skeleton

**Files:**
- Create: `sre_agent/__init__.py`

**Step 1: Create the package directory and init file**

```bash
mkdir -p sre_agent
```

Create `sre_agent/__init__.py`:
```python
"""Self-Healing SRE Agent — pip-installable package."""

__version__ = "1.0.0"
```

**Step 2: Verify Python sees it as a package**

```bash
python -c "import sre_agent; print(sre_agent.__version__)"
```
Expected output: `1.0.0`

**Step 3: Commit**

```bash
git add sre_agent/__init__.py
git commit -m "feat: create sre_agent package skeleton"
```

---

## Task 2: Move core agent files into `sre_agent/`

All five core modules move together so imports stay consistent. We do them all in one step to avoid a broken intermediate state.

**Files:**
- Create: `sre_agent/config.py` (copy of root `config.py`)
- Create: `sre_agent/state.py` (copy of root `state.py`)
- Create: `sre_agent/graph.py` (copy of root `graph.py`, imports updated)
- Create: `sre_agent/agents.py` (copy of root `agents.py`, imports updated)
- Create: `sre_agent/tools.py` (copy of root `tools.py`, imports updated)
- Create: `sre_agent/auto_heal_ci.py` (copy of root `auto_heal_ci.py`, imports updated)
- Delete (after copy confirmed working): root `config.py`, `state.py`, `graph.py`, `agents.py`, `tools.py`, `auto_heal_ci.py`

**Step 1: Copy files into package**

```bash
cp config.py       sre_agent/config.py
cp state.py        sre_agent/state.py
cp tools.py        sre_agent/tools.py
cp agents.py       sre_agent/agents.py
cp graph.py        sre_agent/graph.py
cp auto_heal_ci.py sre_agent/auto_heal_ci.py
```

**Step 2: Update imports in every copied file**

In `sre_agent/tools.py` — change the lazy imports inside functions:
```python
# OLD (inside fetch_logs and open_github_pr):
from config import settings
# NEW:
from sre_agent.config import settings
```

In `sre_agent/agents.py`:
```python
# OLD:
from config import settings
from state import SREAgentState
from tools import fetch_logs, open_github_pr, run_tests
# NEW:
from sre_agent.config import settings
from sre_agent.state import SREAgentState
from sre_agent.tools import fetch_logs, open_github_pr, run_tests
```

In `sre_agent/graph.py`:
```python
# OLD:
from agents import investigator_agent, mechanic_agent, pr_creator_node, validator_node
from config import settings
from state import SREAgentState
# NEW:
from sre_agent.agents import investigator_agent, mechanic_agent, pr_creator_node, validator_node
from sre_agent.config import settings
from sre_agent.state import SREAgentState
```

In `sre_agent/auto_heal_ci.py`:
```python
# OLD:
from graph import sre_graph
from state import create_initial_state
# NEW:
from sre_agent.graph import sre_graph
from sre_agent.state import create_initial_state
```

**Step 3: Verify imports work from package**

```bash
python -c "from sre_agent.config import settings; print('config OK')"
python -c "from sre_agent.state import SREAgentState; print('state OK')"
python -c "from sre_agent.graph import sre_graph; print('graph OK')"
```
Expected: three lines each ending in `OK`

**Step 4: Delete the now-redundant root copies**

```bash
git rm config.py state.py tools.py agents.py graph.py auto_heal_ci.py
```

**Step 5: Commit**

```bash
git add sre_agent/
git commit -m "refactor: move agent modules into sre_agent/ package"
```

---

## Task 3: Update tests to use new import paths

**Files:**
- Modify: `tests/test_config.py`
- Modify: `tests/test_state.py`
- Modify: `tests/test_tools.py`

**Step 1: Update `tests/test_config.py`**

Change all imports at the top:
```python
# OLD:
from config import Settings
# NEW:
from sre_agent.config import Settings
```

The `_fresh_settings` helper and all test bodies are unchanged — only the import line changes.

**Step 2: Update `tests/test_state.py`**

```python
# OLD:
from state import SREAgentState, create_initial_state
# NEW:
from sre_agent.state import SREAgentState, create_initial_state
```

**Step 3: Update `tests/test_tools.py`**

```python
# OLD:
from tools import fetch_logs, open_github_pr, run_tests
# NEW:
from sre_agent.tools import fetch_logs, open_github_pr, run_tests
```

**Step 4: Run the full test suite**

```bash
pytest tests/ -v --tb=short
```
Expected: `15 passed`

**Step 5: Commit**

```bash
git add tests/
git commit -m "fix: update test imports to use sre_agent package paths"
```

---

## Task 4: Create `pyproject.toml`

**Files:**
- Create: `pyproject.toml`

**Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "self-healing-sre-agent"
version = "1.0.0"
description = "AI-powered autonomous incident response: detects CI failures, generates fixes, and opens PRs automatically."
readme = "README.md"
license = { file = "LICENSE" }
requires-python = ">=3.10"
keywords = ["sre", "devops", "ai", "langchain", "langgraph", "self-healing", "github-actions"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries",
]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.6",
    "langgraph==0.2.28",
    "langchain>=0.3.1,<0.4",
    "langchain-groq>=0.2.1",
    "langchain-google-genai>=2.0.4",
    "pydantic>=2.9.2",
    "pydantic-settings>=2.6.0",
    "python-dotenv>=1.0.1",
    "httpx>=0.27.2",
    "typing-extensions>=4.12.2",
    "tenacity>=8.1.0,!=8.4.0",
    "PyGithub>=2.4.0",
    "python-json-logger>=2.0.7",
    "streamlit>=1.39.0",
]

[project.optional-dependencies]
dev = [
    "ruff==0.7.0",
    "pytest>=8.3.3",
    "pytest-asyncio>=0.24.0",
]

[project.scripts]
sre-agent = "sre_agent.cli:main"

[project.urls]
Homepage = "https://github.com/jalpatel11/Self-Healing-SRE-Agent"
Repository = "https://github.com/jalpatel11/Self-Healing-SRE-Agent"
Issues = "https://github.com/jalpatel11/Self-Healing-SRE-Agent/issues"

[tool.setuptools.packages.find]
where = ["."]
include = ["sre_agent*"]
```

**Step 2: Install the package in editable mode**

```bash
pip install -e ".[dev]"
```
Expected: Installs successfully, `sre-agent` command now exists but will error (cli.py not yet created).

**Step 3: Confirm the package is importable**

```bash
python -c "import sre_agent; print(sre_agent.__version__)"
```
Expected: `1.0.0`

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add pyproject.toml for pip packaging"
```

---

## Task 5: Create `sre_agent/cli.py` — the `sre-agent heal` command

**Files:**
- Create: `sre_agent/cli.py`

**Step 1: Write the failing test first**

Add to `tests/test_tools.py` (or create `tests/test_cli.py`):

```python
# tests/test_cli.py
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


def test_cli_missing_groq_key(monkeypatch):
    """sre-agent heal must exit non-zero if GROQ_API_KEY is missing."""
    import os
    env = {k: v for k, v in os.environ.items() if k != "GROQ_API_KEY"}
    result = subprocess.run(
        [sys.executable, "-m", "sre_agent.cli", "heal"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode != 0
```

**Step 2: Run to confirm failure**

```bash
pytest tests/test_cli.py -v
```
Expected: `FAILED` — `sre_agent.cli` does not exist yet.

**Step 3: Write `sre_agent/cli.py`**

```python
"""CLI entry point for the Self-Healing SRE Agent.

Usage:
    sre-agent heal [--run-id RUN_ID] [--repo OWNER/REPO]

All options fall back to environment variables when not supplied:
    --run-id  →  GITHUB_RUN_ID
    --repo    →  GITHUB_REPOSITORY
"""

from __future__ import annotations

import argparse
import os
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sre-agent",
        description=(
            "Self-Healing SRE Agent — automatically investigates CI failures, "
            "generates fixes, and opens GitHub pull requests."
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    heal = sub.add_parser("heal", help="Run the self-healing workflow against a failed CI run.")
    heal.add_argument(
        "--run-id",
        default=os.getenv("GITHUB_RUN_ID", ""),
        help="GitHub Actions run ID of the failed workflow (default: $GITHUB_RUN_ID)",
    )
    heal.add_argument(
        "--repo",
        default=os.getenv("GITHUB_REPOSITORY", ""),
        help="Target repository in OWNER/REPO format (default: $GITHUB_REPOSITORY)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "heal":
        # Validate required env vars before importing heavy deps
        if not os.getenv("GROQ_API_KEY") and not os.getenv("GEMINI_API_KEY"):
            print(
                "[ERROR] GROQ_API_KEY (or GEMINI_API_KEY) must be set.\n"
                "  Export the key or add it to your .env file.\n"
                "  Get a free Groq key at https://console.groq.com",
                file=sys.stderr,
            )
            return 1

        # Inject CLI args back into env so auto_heal_ci picks them up
        if args.run_id:
            os.environ.setdefault("GITHUB_RUN_ID", args.run_id)
        if args.repo:
            os.environ.setdefault("GITHUB_REPOSITORY", args.repo)

        from sre_agent.auto_heal_ci import run_ci_auto_heal  # noqa: PLC0415
        return run_ci_auto_heal()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: Run tests**

```bash
pytest tests/test_cli.py -v
```
Expected: `2 passed`

**Step 5: Smoke-test the installed command**

```bash
sre-agent --help
sre-agent heal --help
```
Expected: Help text printed, exit 0.

**Step 6: Commit**

```bash
git add sre_agent/cli.py tests/test_cli.py
git commit -m "feat: add sre-agent CLI entry point with heal subcommand"
```

---

## Task 6: Fix `fetch_logs` — real GitHub Actions log fetching

**Files:**
- Modify: `sre_agent/tools.py`

**Step 1: Write the failing test**

Add to `tests/test_tools.py`:

```python
def test_fetch_logs_uses_github_api_when_env_vars_set(monkeypatch, tmp_path):
    """When GITHUB_RUN_ID + GITHUB_TOKEN are set, fetch_logs calls GitHub API."""
    import httpx
    import respx  # we won't actually use respx — just mock httpx directly

    # Monkeypatch env
    monkeypatch.setenv("GITHUB_RUN_ID", "999")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")

    # Patch httpx.Client so no real network call
    class FakeResp:
        status_code = 200
        def json(self):
            return {"jobs": [{"id": 42, "conclusion": "failure", "name": "test"}]}
        @property
        def text(self):
            return "FAIL: AssertionError at test_foo.py:10"
        def raise_for_status(self):
            pass

    class FakeClient:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def get(self, url, **kwargs):
            return FakeResp()

    monkeypatch.setattr("httpx.Client", lambda **kw: FakeClient())

    from sre_agent.tools import fetch_logs
    result = fetch_logs.invoke({"time_range": "1h", "severity": "error"})
    assert "FAIL" in result or "AssertionError" in result or "GitHub Actions" in result
```

**Step 2: Run to confirm failure**

```bash
pytest tests/test_tools.py::test_fetch_logs_uses_github_api_when_env_vars_set -v
```
Expected: `FAILED` — current `fetch_logs` only reads a local file.

**Step 3: Rewrite `fetch_logs` in `sre_agent/tools.py`**

Replace the existing `fetch_logs` function body with:

```python
@tool
def fetch_logs(time_range: str = "1h", severity: str = "error") -> str:
    """
    Fetch application logs for investigation.

    Behaviour (in priority order):
    1. If GITHUB_RUN_ID + GITHUB_TOKEN are set → fetch the failing CI job's
       logs via the GitHub Actions API (works in any repo's CI pipeline).
    2. Otherwise → read from the local log file configured by LOG_FILE
       (demo / local development mode).

    Args:
        time_range: Ignored for GitHub API logs; used for local file filtering.
        severity:   Ignored for GitHub API logs; used for local file filtering.

    Returns:
        Log text as a string, or an error message if logs are unavailable.
    """
    import os

    import httpx

    from sre_agent.config import settings

    run_id = os.getenv("GITHUB_RUN_ID", "").strip()
    github_token = os.getenv("GITHUB_TOKEN", settings.github_token or "").strip()
    repo = os.getenv("GITHUB_REPOSITORY", settings.github_repo or "").strip()

    # ── 1. GitHub Actions API path ──────────────────────────────────────────
    if run_id and github_token and repo:
        return _fetch_github_actions_logs(run_id, repo, github_token)

    # ── 2. Local log file (demo / dev mode) ────────────────────────────────
    return _fetch_local_logs(settings.log_file, time_range, severity)


def _fetch_github_actions_logs(run_id: str, repo: str, token: str) -> str:
    """Download logs for failed jobs in a GitHub Actions run."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    base = "https://api.github.com"

    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=30) as client:
            # Get all jobs for this run
            jobs_resp = client.get(f"{base}/repos/{repo}/actions/runs/{run_id}/jobs")
            jobs_resp.raise_for_status()
            jobs = jobs_resp.json().get("jobs", [])

            # Find failed jobs
            failed_jobs = [j for j in jobs if j.get("conclusion") == "failure"]
            if not failed_jobs:
                return (
                    f"=== GitHub Actions Run {run_id} ===\n"
                    "No failed jobs found. All jobs may have passed or been skipped.\n"
                )

            log_sections: list[str] = []
            for job in failed_jobs[:3]:  # cap at 3 failed jobs
                job_id = job["id"]
                job_name = job.get("name", "unknown")

                logs_resp = client.get(f"{base}/repos/{repo}/actions/jobs/{job_id}/logs")
                if logs_resp.status_code == 200:
                    log_sections.append(
                        f"=== Failed Job: {job_name} (ID: {job_id}) ===\n{logs_resp.text}\n"
                    )
                else:
                    log_sections.append(
                        f"=== Failed Job: {job_name} (ID: {job_id}) ===\n"
                        f"Could not retrieve logs (HTTP {logs_resp.status_code}).\n"
                    )

            combined = "\n".join(log_sections)
            return (
                f"=== GitHub Actions CI Logs (Run {run_id}, Repo: {repo}) ===\n\n"
                f"{combined}\n"
                f"=== End of CI Logs ===\n"
                f"Total failed jobs: {len(failed_jobs)}\n"
            )

    except httpx.HTTPError as exc:
        return f"[ERROR] Failed to fetch GitHub Actions logs: {exc}"
    except Exception as exc:
        return f"[ERROR] Unexpected error fetching CI logs: {exc}"


def _fetch_local_logs(log_file: str, time_range: str, severity: str) -> str:
    """Read logs from local file (demo / development mode)."""
    if not os.path.exists(log_file):
        return (
            "No logs found. The application may not have been started yet, "
            "or no errors have occurred. Please ensure the FastAPI app is running "
            "and has received requests."
        )
    try:
        with open(log_file) as f:
            log_lines = f.readlines()

        if not log_lines:
            return "Log file is empty. No errors have been recorded yet."

        if severity.lower() != "all":
            filtered = [l for l in log_lines if severity.upper() in l or "CRITICAL" in l]
        else:
            filtered = log_lines

        limits = {"5m": 10, "15m": 30, "30m": 50, "1h": 100, "6h": 300, "1d": 500}
        max_lines = limits.get(time_range, 100)
        recent = filtered[-max_lines:] if len(filtered) > max_lines else filtered

        if not recent:
            return f"No logs found with severity '{severity}' in the last {time_range}."

        return (
            f"=== Application Logs (Last {time_range}, Severity: {severity}) ===\n\n"
            f"{''.join(recent)}\n"
            f"=== End of Logs ===\n"
            f"Total lines returned: {len(recent)}\n"
        )
    except Exception as exc:
        return f"Error reading logs: {exc}"
```

**Step 4: Run the tests**

```bash
pytest tests/test_tools.py -v
```
Expected: All tools tests pass (including new GitHub API test).

**Step 5: Commit**

```bash
git add sre_agent/tools.py tests/test_tools.py
git commit -m "feat: fetch_logs now reads real GitHub Actions CI logs via API"
```

---

## Task 7: Fix `open_github_pr` — remove hardcoded `file_path="app.py"`

**Files:**
- Modify: `sre_agent/tools.py`
- Modify: `sre_agent/agents.py` (mechanic prompt update)

**Step 1: Write the failing test**

Add to `tests/test_tools.py`:

```python
def test_open_github_pr_has_no_hardcoded_file_path():
    """open_github_pr must not default file_path to 'app.py'."""
    import inspect
    from sre_agent.tools import open_github_pr

    # Get the underlying function signature (unwrap the @tool decorator)
    sig = inspect.signature(open_github_pr.func)
    param = sig.parameters.get("file_path")
    assert param is not None, "file_path parameter must exist"
    # Default must NOT be "app.py"
    assert param.default != "app.py", (
        "file_path must not default to 'app.py' — "
        "the agent should determine the correct file from log analysis"
    )
```

**Step 2: Run to confirm failure**

```bash
pytest tests/test_tools.py::test_open_github_pr_has_no_hardcoded_file_path -v
```
Expected: `FAILED` — current default is `"app.py"`.

**Step 3: Update `open_github_pr` signature in `sre_agent/tools.py`**

Change the function signature from:
```python
def open_github_pr(
    title: str,
    body: str,
    fix_code: str,
    file_path: str = "app.py",
    branch_name: Optional[str] = None
) -> str:
```

To:
```python
def open_github_pr(
    title: str,
    body: str,
    fix_code: str,
    file_path: str = "main.py",
    branch_name: Optional[str] = None
) -> str:
    """
    Create a GitHub Pull Request with the proposed fix.

    Args:
        title:       PR title summarising the fix.
        body:        PR description with root cause and fix explanation.
        fix_code:    Complete fixed file content (not a diff).
        file_path:   Repo-relative path of the file being fixed.
                     The Mechanic agent MUST identify this from the CI logs
                     (e.g. "src/auth.py", "utils/db.py").  Defaults to
                     "main.py" as a safe fallback only.
        branch_name: Branch for the PR (auto-generated from timestamp if None).

    Returns:
        PR URL string if successful, or error/simulation message.
    """
```

**Step 4: Update mechanic agent prompt in `sre_agent/agents.py`**

In the `mechanic_agent` function, find the system prompt string and add the following instruction to it. Look for the section that describes the output format and add:

```python
# Find the system_prompt in mechanic_agent and append this paragraph:
"""
IMPORTANT — file_path:
You MUST identify the exact repository-relative path of the file that
needs to be fixed (e.g. "src/api/routes.py", "tests/test_auth.py").
Read the error traceback in the CI logs to find the correct file.
Always pass this as the `file_path` argument to open_github_pr.
Do NOT assume the file is "app.py".
"""
```

**Step 5: Run the tests**

```bash
pytest tests/ -v --tb=short
```
Expected: All tests pass including the new assertion.

**Step 6: Commit**

```bash
git add sre_agent/tools.py sre_agent/agents.py tests/test_tools.py
git commit -m "fix: remove hardcoded app.py from open_github_pr, agent detects file from logs"
```

---

## Task 8: Move demo files to `demo/`

**Files:**
- Create: `demo/` directory
- Move: `app.py` → `demo/app.py`
- Move: `test_app.py` → `demo/test_app.py`
- Move: `run.sh` → `demo/run.sh`
- Move: `setup.sh` → `demo/setup.sh`
- Create: `demo/README.md`

**Step 1: Create demo directory and move files**

```bash
mkdir -p demo
git mv app.py demo/app.py
git mv test_app.py demo/test_app.py
git mv run.sh demo/run.sh
git mv setup.sh demo/setup.sh
```

**Step 2: Fix the import in `demo/test_app.py`**

`demo/test_app.py` imports from `app` — update to relative import since it's now inside `demo/`:

Open `demo/test_app.py` and change:
```python
# The test imports app directly; update the path for the new location:
# No change needed if tests run from the demo/ directory.
# But add a note at the top:
"""Demo service tests — run from repo root with: pytest demo/test_app.py"""
```

Also update the `app.py` reference in `demo/test_app.py` if there's an explicit import:
```python
# If demo/test_app.py has: import app  or  from app import ...
# It stays the same because both files are now in demo/
# pytest handles the relative import when invoked from demo/
```

**Step 3: Create `demo/README.md`**

```markdown
# Demo Service

This directory contains a simple FastAPI demo service used to demonstrate
the Self-Healing SRE Agent locally.

## Quick Start

```bash
# From repo root
cd demo
pip install fastapi uvicorn

# Terminal 1 — Start the demo service
uvicorn app:app --reload --port 8000

# Terminal 2 — Trigger a crash
curl -H "X-Trigger-Bug: true" http://localhost:8000/api/data

# Terminal 3 — Run the SRE agent against the local logs
sre-agent heal
```

## What it does

- `app.py` — FastAPI service with an intentional bug (missing dict key)
- `test_app.py` — Integration tests for the demo service
- `run.sh` / `setup.sh` — Convenience scripts for local setup

For production use, point the agent at a real GitHub Actions run instead.
```

**Step 4: Run full test suite (excluding demo tests)**

```bash
pytest tests/ -v --tb=short
```
Expected: All 15 + new tests pass. Demo tests in `demo/` are not run (they need the FastAPI service running).

**Step 5: Commit**

```bash
git add demo/
git commit -m "refactor: move demo FastAPI app to demo/ folder, keeping agent core clean"
```

---

## Task 9: Update `Dockerfile` to install the package

**Files:**
- Modify: `Dockerfile`

**Step 1: Update the Dockerfile**

Replace the current Dockerfile content with:

```dockerfile
# ── Stage 1: Build ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy package definition and source
COPY pyproject.toml README.md LICENSE ./
COPY sre_agent/ ./sre_agent/

# Install package + deps into user site-packages for slim-stage copy
RUN pip install --user --no-cache-dir ".[dev]"

# ── Stage 2: Runtime ───────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy package source (needed for editable-style resolution)
COPY sre_agent/ ./sre_agent/
COPY pyproject.toml README.md LICENSE ./

RUN mkdir -p /app/logs

ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_FILE=/app/logs/app_logs.txt

# Default: run the self-healing CLI
CMD ["sre-agent", "heal"]
```

**Step 2: Build and verify**

```bash
docker build -t sre-agent-test .
docker run --rm sre-agent-test sre-agent --help
```
Expected: Help text printed, exit 0.

**Step 3: Commit**

```bash
git add Dockerfile
git commit -m "feat: update Dockerfile to install sre_agent package via pyproject.toml"
```

---

## Task 10: Update CI workflow to validate pip install

**Files:**
- Modify: `.github/workflows/ci.yml`

**Step 1: Add package install validation step to the `test` job**

In `.github/workflows/ci.yml`, inside the `test` job's `steps:` block, after `Install dependencies`, add:

```yaml
      - name: Validate package installs correctly
        run: |
          pip install -e ".[dev]"
          sre-agent --help
          python -c "import sre_agent; print('Package version:', sre_agent.__version__)"
```

Also update the `Install dependencies` step to install both:
```yaml
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -e ".[dev]"
```

**Step 2: Run tests locally to verify nothing is broken**

```bash
pytest tests/ -v --tb=short
```
Expected: All tests pass.

**Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add pip install validation step to test job"
```

---

## Task 11: Update `auto-heal.yml` for external repo use

**Files:**
- Modify: `.github/workflows/auto-heal.yml`

The existing `auto-heal.yml` is hardwired to trigger on the `"CI/CD"` workflow name in THIS repo. Update it to:
1. Also trigger on common workflow names (`"CI"`, `"Build"`, `"Tests"`)
2. Use the pip-installed `sre-agent heal` command

**Step 1: Rewrite `.github/workflows/auto-heal.yml`**

```yaml
name: Auto-Heal on CI Failure

# Triggers when any of the listed workflows fail.
# External repos: copy this file and update the workflows list to match
# your CI workflow name (e.g. "CI", "Build", "Test Suite").
on:
  workflow_run:
    workflows: ["CI", "CI/CD", "Build", "Tests", "Test Suite"]
    types: [completed]
    branches: [main]

jobs:
  auto-heal:
    # Only run when the triggering workflow actually failed
    if: github.event.workflow_run.conclusion == 'failure'
    runs-on: ubuntu-latest

    permissions:
      contents: write
      pull-requests: write
      actions: read

    steps:
      - name: Install self-healing-sre-agent
        run: pip install self-healing-sre-agent

      - name: Run Self-Healing Agent
        id: heal
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_RUN_ID: ${{ github.event.workflow_run.id }}
          LLM_PROVIDER: groq
        run: sre-agent heal

      - name: Report Results
        if: always()
        run: |
          if [ "${{ steps.heal.outcome }}" = "success" ]; then
            echo "✓ Self-healing agents successfully executed"
          else
            echo "✗ Self-healing agents encountered errors"
          fi

      - name: Create Issue on Total Failure
        if: failure()
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `[ALERT] Self-Healing Failed for Run ${context.payload.workflow_run.id}`,
              body: [
                `The CI workflow failed and the self-healing agent was unable to auto-fix.`,
                ``,
                `Failed Workflow: ${context.payload.workflow_run.html_url}`,
                ``,
                `**To fix manually:** Review the failed run and apply a fix.`,
                ``,
                `**To configure the agent:** Ensure \`GROQ_API_KEY\` is set in repository secrets.`,
              ].join('\n'),
              labels: ['sre-agent-failed', 'ci-failure'],
            })
```

**Step 2: Commit**

```bash
git add .github/workflows/auto-heal.yml
git commit -m "feat: update auto-heal workflow to use pip-installed sre-agent CLI"
```

---

## Task 12: Final integration check + push

**Step 1: Run the complete test suite**

```bash
pytest tests/ -v --tb=short
```
Expected: All tests pass (15 original + 2 new CLI tests + new tools tests).

**Step 2: Verify the installed CLI works end-to-end**

```bash
# Install in editable mode if not already
pip install -e ".[dev]"

# Verify CLI
sre-agent --help
sre-agent heal --help

# Verify package import
python -c "
from sre_agent.config import settings
from sre_agent.state import SREAgentState, create_initial_state
from sre_agent.graph import sre_graph
from sre_agent.tools import fetch_logs, run_tests, open_github_pr
from sre_agent.cli import main
print('All imports OK')
"
```
Expected: `All imports OK`

**Step 3: Run ruff to ensure no lint regressions**

```bash
ruff check sre_agent/ tests/ --output-format=github
```
Expected: No errors.

**Step 4: Push the branch**

```bash
git push origin feature/pip-package
```

**Step 5: Open a Pull Request**

```bash
gh pr create \
  --title "feat: package as pip-installable sre-agent CLI" \
  --body "$(cat <<'EOF'
## Summary
- Restructures agent code into `sre_agent/` Python package
- Adds `pyproject.toml` for `pip install self-healing-sre-agent`
- Adds `sre-agent heal` CLI command
- `fetch_logs` now fetches real GitHub Actions CI logs via API
- Removes hardcoded `file_path='app.py'` from `open_github_pr`
- Moves demo FastAPI service to `demo/`
- Updates `auto-heal.yml` to use `pip install` + `sre-agent heal`

## Integration (for external repos)
1. Add `GROQ_API_KEY` to GitHub Secrets
2. Copy `.github/workflows/auto-heal.yml` into their repo
3. Done

## Test plan
- [ ] `pip install -e .` succeeds
- [ ] `sre-agent --help` prints usage
- [ ] All 15+ tests pass
- [ ] CI pipeline green (lint → test → build)
EOF
)"
```

---

## Summary of all files changed

| File | Action |
|------|--------|
| `sre_agent/__init__.py` | Created |
| `sre_agent/cli.py` | Created |
| `sre_agent/config.py` | Moved from root |
| `sre_agent/state.py` | Moved from root |
| `sre_agent/agents.py` | Moved from root + mechanic prompt updated |
| `sre_agent/tools.py` | Moved from root + `fetch_logs` GitHub API + `open_github_pr` fix |
| `sre_agent/graph.py` | Moved from root |
| `sre_agent/auto_heal_ci.py` | Moved from root |
| `pyproject.toml` | Created |
| `demo/app.py` | Moved from root |
| `demo/test_app.py` | Moved from root |
| `demo/run.sh` | Moved from root |
| `demo/setup.sh` | Moved from root |
| `demo/README.md` | Created |
| `tests/test_config.py` | Imports updated |
| `tests/test_state.py` | Imports updated |
| `tests/test_tools.py` | Imports updated + new tests |
| `tests/test_cli.py` | Created |
| `Dockerfile` | Updated to install package |
| `.github/workflows/ci.yml` | Added pip install validation |
| `.github/workflows/auto-heal.yml` | Rewritten for external use |

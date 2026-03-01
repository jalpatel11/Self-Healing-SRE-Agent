# Design: `self-healing-sre-agent` pip Package

**Date:** 2026-02-28
**Branch:** `feature/pip-package`
**Status:** Approved

---

## Goal

Transform the Self-Healing SRE Agent from a standalone repo into a distributable pip package (`self-healing-sre-agent`) so any Python repo can self-heal on CI failure with minimal setup.

---

## User Experience (End State)

**Target repo owner does 3 things:**

1. Add `GROQ_API_KEY` to their GitHub Secrets
2. Add `.github/workflows/auto-heal.yml`:

```yaml
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]

jobs:
  auto-heal:
    if: github.event.workflow_run.conclusion == 'failure'
    runs-on: ubuntu-latest
    steps:
      - run: pip install self-healing-sre-agent
      - run: sre-agent heal
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

3. Done. When their CI fails → agent investigates → opens PR with fix.

**Also works from terminal:**

```bash
pip install self-healing-sre-agent
GROQ_API_KEY=gsk_... GITHUB_TOKEN=ghp_... sre-agent heal --run-id 12345678
```

---

## Architecture

### New Directory Structure

```
Self-Healing-SRE-Agent/
├── pyproject.toml          # Package metadata, CLI entry point, deps
├── sre_agent/              # Main package directory
│   ├── __init__.py         # Package init + version
│   ├── cli.py              # `sre-agent heal` CLI entry point
│   ├── config.py           # Settings (moved from root)
│   ├── state.py            # LangGraph state (moved from root)
│   ├── agents.py           # Agent nodes (moved from root)
│   ├── tools.py            # Tools: fetch_logs, run_tests, open_github_pr
│   ├── graph.py            # LangGraph StateGraph (moved from root)
│   └── auto_heal_ci.py     # CI orchestration logic (moved from root)
├── demo/                   # Demo FastAPI service (moved from root)
│   ├── app.py
│   ├── test_app.py
│   ├── run.sh
│   ├── setup.sh
│   └── README.md
├── tests/                  # Test suite (imports updated)
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_state.py
│   └── test_tools.py
├── .github/
│   └── workflows/
│       ├── ci.yml          # Updated to test pip install
│       └── auto-heal.yml   # Updated to use new package
├── Dockerfile              # Updated: installs package with pip
├── docker-compose.yml      # Unchanged
├── requirements.txt        # Kept for development; pyproject.toml is canonical
└── ruff.toml               # Unchanged
```

---

## Core Changes

### 1. `pyproject.toml` (NEW)

Standard modern Python packaging. Defines:
- Package name: `self-healing-sre-agent`
- Version: `1.0.0`
- CLI entry point: `sre-agent = "sre_agent.cli:main"`
- All dependencies (same as `requirements.txt`)
- Build backend: `setuptools`

### 2. `sre_agent/cli.py` (NEW)

CLI entry point for `sre-agent heal`:
- Parses optional `--run-id` and `--repo` flags
- Falls back to env vars (`GITHUB_RUN_ID`, `GITHUB_REPOSITORY`)
- Calls `run_ci_auto_heal()` from `auto_heal_ci.py`
- Returns exit code (0 = success, 1 = failure)

### 3. `sre_agent/tools.py` — Fix `fetch_logs`

**Current:** Reads local `app_logs.txt` file.
**New:** When `GITHUB_RUN_ID` and `GITHUB_TOKEN` are set, fetch actual CI logs via GitHub API:

```
GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs
→ find failed job ID
GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs
→ return log text
```

Falls back to local log file if env vars not set (preserves demo mode).

### 4. `sre_agent/tools.py` — Fix `open_github_pr`

**Current:** `file_path="app.py"` hardcoded default.
**New:** `file_path` has no default — the Mechanic agent must specify which file to fix based on log analysis. The tool accepts whatever file the agent identifies.

Updated mechanic agent prompt instructs it to include `file_path` in its output.

### 5. Move demo files → `demo/`

Files moved (not deleted):
- `app.py` → `demo/app.py`
- `test_app.py` → `demo/test_app.py`
- `run.sh` → `demo/run.sh`
- `setup.sh` → `demo/setup.sh`

`demo/README.md` added explaining how to run the demo service.

### 6. Update all imports

All internal imports updated from flat `from config import settings` to `from sre_agent.config import settings`.

### 7. Update `tests/` imports

All test files updated to import from `sre_agent.*`.

### 8. Update `Dockerfile`

Instead of copying individual `.py` files, install the package:
```dockerfile
COPY pyproject.toml .
COPY sre_agent/ ./sre_agent/
RUN pip install -e .
CMD ["sre-agent", "heal"]
```

### 9. Update `.github/workflows/ci.yml`

Add a packaging validation step:
```yaml
- name: Validate package installs
  run: pip install -e . && sre-agent --help
```

---

## Data Flow (unchanged)

```
CI Failure
    ↓
sre-agent heal
    ↓
fetch_logs → GitHub API (real CI logs)
    ↓
investigator_agent → LLM analysis
    ↓
mechanic_agent → fix code + file_path
    ↓
validator_node → AST + syntax check
    ↓ (pass)
open_github_pr → GitHub PR created
```

---

## What Does NOT Change

- LangGraph workflow (`graph.py`) — unchanged
- Agent prompts (`agents.py`) — unchanged (except mechanic gets file_path instruction)
- State schema (`state.py`) — unchanged
- Config system (`config.py`) — unchanged
- 15 existing tests — all pass after import updates
- Docker + docker-compose — minor updates only

---

## Success Criteria

- [ ] `pip install -e .` installs successfully
- [ ] `sre-agent heal --help` works
- [ ] All 15 tests pass with new import paths
- [ ] `fetch_logs` returns real GitHub Actions CI logs when env vars set
- [ ] `open_github_pr` no longer has `app.py` hardcoded
- [ ] Demo mode still works from `demo/` folder
- [ ] CI pipeline (lint → test → build) stays green

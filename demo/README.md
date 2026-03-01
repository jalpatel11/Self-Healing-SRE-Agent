# Demo Service

This directory contains a simple FastAPI demo service used to demonstrate
the Self-Healing SRE Agent locally — it intentionally has a bug that the
agent detects and fixes.

## Quick Start

```bash
# From repo root — Terminal 1: Start the demo service
cd demo && pip install fastapi uvicorn
uvicorn app:app --reload --port 8000

# Terminal 2: Trigger the intentional crash
curl -H "X-Trigger-Bug: true" http://localhost:8000/api/data

# Terminal 3: Run the SRE agent against the local logs
cd ..
sre-agent heal
```

## What it does

- `app.py` — FastAPI service with an intentional `KeyError` bug (missing dict key)
- `test_app.py` — Integration tests for the demo service
- `run.sh` / `setup.sh` — Convenience scripts for local setup

## For production use

Point the agent at a real GitHub Actions run instead of the local log file:

```bash
GROQ_API_KEY=gsk_...        \
GITHUB_TOKEN=ghp_...        \
GITHUB_REPOSITORY=org/repo  \
GITHUB_RUN_ID=12345678      \
sre-agent heal
```

# Production-Grade Upgrade Design
**Date:** 2026-02-28
**Project:** Self-Healing SRE Agent
**Status:** Approved

---

## Context

The project is a working proof-of-concept with excellent architecture (LangGraph multi-agent, self-correction loop, LangSmith observability) but has multiple gaps that prevent real-world use:

- All LLM model names, ports, file paths, and iteration limits are hardcoded in source
- The Mechanic and Investigator agents use `ChatAnthropic` + `ChatOpenAI` (proprietary, expensive)
- The PR title/body is hardcoded to the demo bug (`"Fix KeyError in /api/data endpoint"`)
- The validator (`run_tests`) checks for one specific bug pattern, can't work on real codebases
- No Dockerfile, no docker-compose, no CI/CD
- No env validation on startup (silently ignores missing keys)
- `datetime.utcnow()` deprecated
- In-memory LangGraph state (lost on restart)
- No log rotation (app_logs.txt grows unbounded)
- No test suite

**Goal:** Replace proprietary LLMs with free providers (Groq + Gemini), fix all hardcoded values, make the validator generic, and wrap everything in Docker + GitHub Actions CI/CD.

---

## LLM Strategy

**Primary:** Groq (Llama 3.1 70B) via `langchain-groq`
**Fallback:** Google Gemini 1.5 Flash via `langchain-google-genai`
**Switch:** `LLM_PROVIDER` env var (`groq` | `gemini`)

Replaces both `langchain-anthropic` and `langchain-openai`.

---

## Architecture

```
docker-compose up
├── sre-app    (FastAPI :8000) — demo buggy app
├── sre-agent  (python main.py) — LangGraph workflow
└── sre-ui     (Streamlit :8501) — web interface
     ↕ shared named volume: sre_logs → /app/logs/

GitHub Actions:
push/PR  →  lint (ruff)  →  test (pytest)  →  build Docker  →  push GHCR (main only)
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `config.py` | Pydantic BaseSettings — all env vars, startup validation |
| `Dockerfile` | Multi-stage build (builder → runtime) |
| `docker-compose.yml` | Orchestrate sre-app + sre-agent + sre-ui |
| `.dockerignore` | Exclude venv, __pycache__, .env, .git |
| `.github/workflows/ci.yml` | lint → test → build → push to GHCR |
| `tests/__init__.py` | Test package |
| `tests/test_config.py` | Validate config loading and validation |
| `tests/test_tools.py` | Test fetch_logs, run_tests (generic AST) |
| `tests/test_state.py` | Test create_initial_state() |

---

## Files to Modify

| File | Changes |
|------|---------|
| `requirements.txt` | Add: langchain-groq, langchain-google-genai, pydantic-settings, tenacity, ruff, pytest, pytest-asyncio; Remove: langchain-anthropic, langchain-openai |
| `.env.example` | Replace all keys with new schema |
| `state.py` | Fix `datetime.utcnow()` → `datetime.now(timezone.utc)` |
| `agents.py` | Use config for model/provider, dynamic PR content, tenacity retry, remove OpenAI import |
| `tools.py` | Generic AST validator, log path from config |
| `graph.py` | `max_iterations` from config |
| `app.py` | RotatingFileHandler, log path from config |
| `main.py` | Remove placeholder string checks, use config |
| `ui.py` | Remove placeholder checks, ports from config |

---

## config.py Design

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    # LLM
    llm_provider: str = "groq"          # "groq" | "gemini"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # GitHub
    github_token: str = ""
    github_repo: str = ""
    github_branch: str = "main"

    # App
    app_port: int = 8000
    log_file: str = "app_logs.txt"
    max_iterations: int = 3

    # LangSmith (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "sre-agent"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @field_validator("groq_api_key")
    def validate_groq_key(cls, v, info):
        if info.data.get("llm_provider") == "groq" and not v:
            raise ValueError("GROQ_API_KEY required when LLM_PROVIDER=groq")
        return v

    @field_validator("gemini_api_key")
    def validate_gemini_key(cls, v, info):
        if info.data.get("llm_provider") == "gemini" and not v:
            raise ValueError("GEMINI_API_KEY required when LLM_PROVIDER=gemini")
        return v

settings = Settings()
```

---

## agents.py — LLM Factory

```python
from config import settings
from tenacity import retry, stop_after_attempt, wait_exponential

def get_llm(temperature=0):
    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(api_key=settings.groq_api_key, model=settings.groq_model, temperature=temperature)
    elif settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(google_api_key=settings.gemini_api_key, model=settings.gemini_model, temperature=temperature)
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def invoke_with_retry(llm, messages):
    return llm.invoke(messages)
```

**Dynamic PR content:**
```python
# Extract from state instead of hardcoding
root_cause = state.get("root_cause", "Unknown root cause")
title = f"[Automated Fix] {root_cause[:80]}"
body = PR_BODY_TEMPLATE.format(
    root_cause=root_cause,
    test_results=state.get("test_results", ""),
    timestamp=datetime.now(timezone.utc).isoformat(),
)
```

---

## tools.py — Generic Validator

Replace hardcoded pattern checking with a generic AST-based approach:

```python
def run_tests(code: str, original_code: str) -> dict:
    results = {"passed": False, "errors": []}

    # 1. Syntax check
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        results["errors"].append(f"Syntax error: {e}")
        return results

    # 2. Preserve all original function signatures
    original_functions = {node.name for node in ast.walk(ast.parse(original_code)) if isinstance(node, ast.FunctionDef)}
    fixed_functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    missing = original_functions - fixed_functions
    if missing:
        results["errors"].append(f"Missing functions from original: {missing}")
        return results

    # 3. No bare except clauses (common antipattern)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            results["errors"].append("Bare 'except:' found — use specific exception types")

    results["passed"] = len(results["errors"]) == 0
    return results
```

---

## Dockerfile

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
RUN mkdir -p /app/logs
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## docker-compose.yml

```yaml
version: '3.9'
services:
  sre-app:
    build: .
    ports: ["8000:8000"]
    volumes: [logs:/app/logs]
    env_file: .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      retries: 3

  sre-agent:
    build: .
    command: python main.py
    volumes: [logs:/app/logs]
    env_file: .env
    depends_on:
      sre-app: {condition: service_healthy}

  sre-ui:
    build: .
    command: streamlit run ui.py --server.port 8501 --server.address 0.0.0.0
    ports: ["8501:8501"]
    env_file: .env
    depends_on: [sre-app]

volumes:
  logs:
```

---

## GitHub Actions (.github/workflows/ci.yml)

```yaml
name: CI
on:
  push: {branches: [main]}
  pull_request: {branches: [main]}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install ruff && ruff check .

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt pytest
      - run: pytest tests/ -v
        env:
          LLM_PROVIDER: groq
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}

  build-and-push:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        if: github.ref == 'refs/heads/main'
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: ${{ github.ref == 'refs/heads/main' }}
          tags: ghcr.io/${{ github.repository }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## Updated .env.example

```bash
# LLM Provider (groq | gemini)
LLM_PROVIDER=groq

# Groq (free at console.groq.com)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile

# Gemini (free at aistudio.google.com) — used when LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# GitHub (for real PR creation)
GITHUB_TOKEN=your_github_pat_here
GITHUB_REPO=yourusername/yourrepo
GITHUB_BRANCH=main

# App
APP_PORT=8000
LOG_FILE=/app/logs/app_logs.txt
MAX_ITERATIONS=3

# LangSmith (optional — free tier at smith.langchain.com)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=sre-agent
```

---

## Verification

1. **Config loads:** `python -c "from config import settings; print(settings.llm_provider)"`
2. **Tests pass:** `pytest tests/ -v`
3. **Lint passes:** `ruff check .`
4. **Docker builds:** `docker build -t sre-agent .`
5. **Compose runs:** `docker-compose up` — all 3 services healthy
6. **End-to-end:** Visit http://localhost:8501, trigger crash, watch workflow, verify real PR created on GitHub
7. **CI/CD:** Push to main branch → verify GitHub Actions passes all 3 jobs and pushes to GHCR

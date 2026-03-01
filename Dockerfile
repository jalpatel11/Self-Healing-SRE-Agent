# ── Stage 1: Build ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy package definition and source
COPY pyproject.toml README.md LICENSE ./
COPY sre_agent/ ./sre_agent/

# Install package + runtime deps into user site-packages for slim-stage copy
RUN pip install --user --no-cache-dir .

# ── Stage 2: Runtime ───────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy package source (required for import resolution)
COPY sre_agent/ ./sre_agent/
COPY pyproject.toml README.md LICENSE ./

RUN mkdir -p /app/logs

ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_FILE=/app/logs/app_logs.txt

# Default: run the self-healing CLI
CMD ["sre-agent", "heal"]

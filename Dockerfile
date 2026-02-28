# ============================================================
# Stage 1: Build — install Python dependencies
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ============================================================
# Stage 2: Runtime — lean production image
# ============================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application source (excludes what's in .dockerignore)
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_FILE=/app/logs/app_logs.txt

EXPOSE 8000

# Default: run the FastAPI demo app (overridden in docker-compose for other services)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

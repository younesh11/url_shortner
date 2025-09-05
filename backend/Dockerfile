
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

# Small base utils & certs
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Dependencies (use requirements.txt if present)
COPY backend/requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ -f /tmp/requirements.txt ]; then \
      pip install -r /tmp/requirements.txt; \
    else \
      pip install "fastapi>=0.111" "uvicorn[standard]>=0.29" \
                  "sqlalchemy>=2.0" "pydantic>=2.5" "python-dotenv>=1.0"; \
    fi

# App code
COPY backend /app/backend

# Data dir for SQLite and sane default DATABASE_URL
RUN mkdir -p /data && useradd -m -u 1000 appuser && chown -R appuser:appuser /data /app
ENV DATABASE_URL=sqlite:////data/urls.db

# Make package-style imports work (app.*)
ENV PYTHONPATH=/app/backend

USER appuser

EXPOSE 8000

# Prestart: create tables (no-ops if already exist), then serve
CMD sh -c "python -m app.db.init_db && uvicorn app.main:app --host 0.0.0.0 --port 8000"

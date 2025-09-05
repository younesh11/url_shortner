FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# (Optional) system certs; keep image small
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# If you have frontend/requirements.txt we’ll use it; otherwise install minimal deps
COPY frontend/requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ -f /tmp/requirements.txt ]; then \
        pip install -r /tmp/requirements.txt; \
    else \
        pip install "streamlit>=1.36" "requests>=2.31" "python-dotenv>=1.0"; \
    fi

# Copy only the frontend app
COPY frontend /app/frontend

# Streamlit runtime settings
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHERUSAGESTATS=false

EXPOSE 8501
WORKDIR /app/frontend

# Run!
CMD ["streamlit", "run", "streamlit_app.py"]

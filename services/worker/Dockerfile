# ─────────────────────────────────────────────────────────────
# FastUI Worker Dockerfile — Cloud Run (Playwright + Chromium)
# ─────────────────────────────────────────────────────────────
# Uses python:3.11-slim with the Playwright browser install baked in.
# Deployed as a private, IAM-authenticated Google Cloud Run service.
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PORT=8001 \
    ENVIRONMENT=production \
    HEADLESS_BROWSER=true

WORKDIR /app

# Install system dependencies required by Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium and all Linux system libraries
RUN playwright install --with-deps chromium

# Copy application source code
COPY . .

# Expose the worker port
EXPOSE 8001

# Start the FastAPI worker with a single worker process
# Cloud Run scales by spinning up more container instances
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001} --workers 1"]

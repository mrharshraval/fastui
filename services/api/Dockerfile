# ─────────────────────────────────────────────────────────────
# FastUI Production Dockerfile (FastAPI + Playwright Worker)
# ─────────────────────────────────────────────────────────────
# Uses official Microsoft Playwright image pre-baked with all
# required Linux shared libraries, fonts, and Chromium dependencies.
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PORT=8000

WORKDIR /app

# Install system utilities needed for building C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium and its Linux system libraries with root privileges
RUN playwright install --with-deps chromium

# Copy application source code
COPY . .

# Expose standard container port
EXPOSE 8000

# Run database migrations and start production ASGI server
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]

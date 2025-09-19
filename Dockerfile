# syntax=docker/dockerfile:1
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (leverage cache)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app
COPY . /app

# Default environment
ENV ADK_LOG_LEVEL=INFO \
    NTH_API_HOST=0.0.0.0 \
    NTH_API_PORT=8002 \
    NTH_API_BASE_URL=http://nth-api:8002 \
    ADK_PORT=8000 \
    ADK_HOST=0.0.0.0

# Expose ports
EXPOSE 8000 8002

# Start the ADK web server by default
# Use: docker compose to also start the nth-api process as a separate service
CMD ["bash", "-lc", "adk web --host=$ADK_HOST --port=$ADK_PORT --no-reload"] 
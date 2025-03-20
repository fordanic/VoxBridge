FROM python:3.11-slim

WORKDIR /app

# Common dependencies for all services
COPY docker/base/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add common utilities and ffmpeg
RUN apt-get update && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m voxbridge
USER voxbridge

# Common environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VOXBRIDGE_ENV=development

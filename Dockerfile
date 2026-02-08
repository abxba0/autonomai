FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY requirements/ requirements/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e ".[web,distributed]"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/instructions /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import redis; r = redis.Redis.from_url('${REDIS_URL:-redis://localhost:6379}'); r.ping()" || exit 1

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "web.api_secure:app", "--host", "0.0.0.0", "--port", "8000"]

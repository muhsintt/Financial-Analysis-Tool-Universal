# Financial Analysis Tool - Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/backend/data /app/backend/uploads

# Set working directory to backend
WORKDIR /app/backend

# Expose port (internal - NGINX handles external access)
EXPOSE 5000

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/backend/data /app/backend/uploads && \
    chmod +x /docker-entrypoint.sh

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/status')" || exit 1

# Set entrypoint and default command
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "run:app"]

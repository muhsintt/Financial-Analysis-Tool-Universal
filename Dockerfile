# Financial Analysis Tool - Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV SSL_ENABLED=false

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Copy startup script
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/backend/data /app/backend/uploads /app/certs

# Set working directory to backend
WORKDIR /app/backend

# Expose ports (HTTP and HTTPS)
EXPOSE 5000 5443

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /docker-entrypoint.sh && \
    chmod 755 /app/certs

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; import ssl; ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE; urllib.request.urlopen('https://localhost:5443/api/status', context=ctx) if '${SSL_ENABLED}' == 'true' else urllib.request.urlopen('http://localhost:5000/api/status')" || exit 1

# Run the application with gunicorn via entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

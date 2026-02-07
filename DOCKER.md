# Docker Deployment Guide

## Architecture

This setup uses **NGINX as a reverse proxy** to handle SSL/HTTPS, providing:
- Better security (SSL termination at NGINX)
- Better performance (static file caching, connection handling)
- Standard ports (80 for HTTP, 443 for HTTPS)
- Automatic HTTP to HTTPS redirect

```
                    ┌─────────────────────────────────────────┐
                    │              Docker Network             │
Internet ──────────►│                                         │
   :80/:443         │  ┌─────────┐         ┌──────────────┐  │
                    │  │  NGINX  │────────►│  Flask App   │  │
                    │  │ :80/:443│  :5000  │  (Gunicorn)  │  │
                    │  └─────────┘         └──────────────┘  │
                    │       │                     │          │
                    │       ▼                     ▼          │
                    │   ./certs/          ./data/ ./uploads/ │
                    └─────────────────────────────────────────┘
```

## Quick Start

### HTTP Only (Development)

```bash
# Build and start
docker compose up -d --build

# View logs
docker compose logs -f
```

Access at: **http://localhost** (port 80)

### HTTPS with Self-Signed Certificate

```bash
# Create .env file with SSL enabled
echo "SSL_ENABLED=true" > .env

# Build and start
docker compose up -d --build
```

Access at: **https://localhost** (port 443)

> ⚠️ Your browser will show a security warning for self-signed certificates. This is expected for development.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session secret key | `change-me-in-production` |
| `FLASK_ENV` | Environment mode | `production` |
| `SSL_ENABLED` | Enable HTTPS via NGINX | `false` |

### Production Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set a secure `SECRET_KEY`:
   ```bash
   # Generate a secure key
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. Enable SSL:
   ```bash
   SSL_ENABLED=true
   ```

4. Start the containers:
   ```bash
   docker compose up -d --build
   ```

## Data Persistence

The following directories are mounted as volumes:

| Local Path | Container Path | Purpose |
|------------|----------------|---------|
| `./data` | `/app/backend/data` | SQLite database |
| `./uploads` | `/app/backend/uploads` | Uploaded files |
| `./certs` | `/etc/nginx/ssl` | SSL certificates |

## SSL/HTTPS Configuration

### Option 1: Auto-generated Self-Signed Certificate (Development)

Simply enable SSL - certificates are generated automatically:

```bash
# In .env file
SSL_ENABLED=true

# Rebuild
docker compose up -d --build
```

### Option 2: Your Own Certificates (Production)

1. Place your certificates in the `./certs` directory:
   ```
   ./certs/cert.pem    # Your SSL certificate
   ./certs/key.pem     # Your private key
   ```

2. Enable SSL in `.env`:
   ```bash
   SSL_ENABLED=true
   ```

3. Start the containers:
   ```bash
   docker compose up -d --build
   ```

### Option 3: Let's Encrypt (Production)

```bash
# Generate certificate with certbot
sudo certbot certonly --standalone -d yourdomain.com

# Copy to certs directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./certs/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./certs/key.pem

# Set permissions
sudo chown $USER:$USER ./certs/*.pem

# Enable SSL
echo "SSL_ENABLED=true" >> .env

# Start containers
docker compose up -d --build
```

## Useful Commands

```bash
# View container status
docker compose ps

# View all logs
docker compose logs -f

# View NGINX logs only
docker compose logs -f nginx

# View App logs only
docker compose logs -f app

# Restart all containers
docker compose restart

# Stop and remove containers
docker compose down

# Rebuild after code changes
docker compose up -d --build

# Enter the app container shell
docker compose exec app /bin/bash

# Enter the nginx container shell
docker compose exec nginx /bin/sh

# Check container health
docker inspect --format='{{.State.Health.Status}}' financial-analysis-app
```

## Troubleshooting

### Containers won't start

Check the logs for errors:
```bash
docker compose logs
```

### NGINX won't start (SSL enabled)

Check if certificates exist and are readable:
```bash
ls -la ./certs/
```

### Cannot access the application

1. Check if containers are running:
   ```bash
   docker compose ps
   ```

2. Check NGINX logs:
   ```bash
   docker compose logs nginx
   ```

3. Verify ports are not in use:
   ```bash
   netstat -an | findstr :80
   netstat -an | findstr :443
   ```

### Database issues

The SQLite database is stored in `./data`. To reset:
```bash
docker compose down
rm -rf ./data/*.db
docker compose up -d
```

### Permission issues (Linux/Mac)

Ensure directories are writable:
```bash
chmod -R 755 ./data ./uploads ./certs
```

## Ports

| Port | Protocol | When |
|------|----------|------|
| 80 | HTTP | Always (redirects to HTTPS when SSL enabled) |
| 443 | HTTPS | When `SSL_ENABLED=true` |

## Security Notes

- The Flask app runs as a non-root user inside the container
- NGINX handles all external traffic and SSL termination
- Internal communication between NGINX and Flask uses HTTP on an isolated Docker network
- Security headers (HSTS, X-Frame-Options, etc.) are set by NGINX

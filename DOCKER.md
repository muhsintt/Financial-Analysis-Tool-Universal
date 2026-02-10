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

## Data Persistence & Volumes

### Persistent Storage

The application uses **Docker named volumes** to ensure data persistence across container rebuilds. Your data is safe even when updating or recreating containers.

**Volumes:**
- `financial-analysis-tool_app_data` - Database and application data
- `financial-analysis-tool_app_uploads` - Uploaded CSV/Excel files

**What's Persisted:**
- SQLite database with all transactions, categories, budgets, users
- Uploaded bank statement files
- Activity logs and configuration settings
- SSL certificates (auto-generated)

### Update Containers (Preserves Data)

Update to the latest version while keeping all your data:

**Windows:**
```batch
update.bat
```

**macOS/Linux:**
```bash
./update.sh
```

The update script will:
- Optionally create a backup before updating
- Pull the latest Docker images
- Rebuild containers without cache
- Preserve all your financial data
- Perform health checks

### Backup & Restore

**Create Backup:**
```bash
# Windows
backup.bat backup

# macOS/Linux  
./backup.sh backup
```

**List Backups:**
```bash
# Windows
backup.bat list

# macOS/Linux
./backup.sh list
```

**Restore from Backup:**
```bash
# Windows
backup.bat restore -f path\to\backup.tar.gz

# macOS/Linux
./backup.sh restore -f path/to/backup.tar.gz
```

**Clean Old Backups:**
```bash
# Windows
backup.bat clean

# macOS/Linux  
./backup.sh clean
```

## Data Persistence (Legacy/Development)

For development or direct file access, you can use the override file:

## Data Persistence (Legacy/Development)

For development or direct file access, you can use the override file:

```bash
# Use bind mounts for development
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

This creates local directories that you can access directly:
- `./data/` - Database files  
- `./uploads/` - Uploaded files

### Volume Management

**View Volumes:**
```bash
docker volume ls | grep financial-analysis-tool
```

**Inspect Volume Contents:**
```bash
# Database volume
docker run --rm -v financial-analysis-tool_app_data:/data alpine ls -la /data

# Uploads volume
docker run --rm -v financial-analysis-tool_app_uploads:/data alpine ls -la /data
```

**Manual Backup (Advanced):**
```bash
# Backup database volume
docker run --rm -v financial-analysis-tool_app_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/manual_db.tar.gz -C /data .

# Backup uploads volume  
docker run --rm -v financial-analysis-tool_app_uploads:/data -v $(pwd)/backups:/backup alpine tar czf /backup/manual_uploads.tar.gz -C /data .
```

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

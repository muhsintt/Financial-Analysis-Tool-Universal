# Docker Deployment Guide

## Quick Start

### Build and run with Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

The application will be available at: **http://localhost:5000**

With HTTPS enabled: **https://localhost:5443**

### Build and run with Docker only

```bash
# Build the image
docker build -t financial-analysis-tool .

# Run the container
docker run -d \
  --name financial-analysis-tool \
  -p 5000:5000 \
  -v $(pwd)/data:/app/backend/data \
  -v $(pwd)/uploads:/app/backend/uploads \
  financial-analysis-tool
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session secret key | `change-me-in-production` |
| `FLASK_ENV` | Environment mode | `production` |
| `SSL_ENABLED` | Enable HTTPS | `false` |
| `SSL_CERT_FILE` | Path to SSL certificate | `/app/certs/cert.pem` |
| `SSL_KEY_FILE` | Path to SSL private key | `/app/certs/key.pem` |

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

3. Start the container:
   ```bash
   docker-compose up -d --build
   ```

## Data Persistence

The following directories are mounted as volumes to persist data:

- `./certs` → `/app/certs` (SSL certificates)

## HTTPS / SSL Configuration

### Option 1: Auto-generated Self-Signed Certificate (Development)

Enable SSL and let the container generate a self-signed certificate:

```bash
# In .env file
SSL_ENABLED=true
```

```bash
docker-compose up -d --build
```

Access the app at: **https://localhost:5443**

> ⚠️ Your browser will show a security warning for self-signed certificates. This is expected for development.

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

3. Start the container:
   ```bash
   docker-compose up -d --build
   ```

### Option 3: Let's Encrypt (Production)

```bash
# Generate certificate with certbot
certbot certonly --standalone -d yourdomain.com

# Copy to certs directory
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./certs/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./certs/key.pem

# Enable SSL
echo "SSL_ENABLED=true" >> .env

# Start container
docker-compose up -d --build
```
- `./data` → `/app/backend/data` (SQLite database)
- `./uploads` → `/app/backend/uploads` (Uploaded files)

## Useful Commands

```bash
# View container status
docker-compose ps

# View logs
docker-compose logs -f financial-analysis-tool

# Restart the container
docker-compose restart

# Stop and remove containers
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Enter the container shell
docker-compose exec financial-analysis-tool /bin/bash

# Check container health
docker inspect --format='{{.State.Health.Status}}' financial-analysis-tool
```

## Troubleshooting

### Container won't start
Check the logs for errors:
```bash
docker-compose logs financial-analysis-tool
```

### Database issues
The SQLite database is stored in the `./data` directory. To reset:
```bash
docker-compose down
rm -rf ./data/*.db
docker-compose up -d
```

### Permission issues
Ensure the data and uploads directories are writable:
```bash
chmod -R 777 ./data ./uploads
```

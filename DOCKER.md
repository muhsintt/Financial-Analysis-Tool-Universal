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

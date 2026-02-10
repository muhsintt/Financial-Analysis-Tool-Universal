#!/bin/bash

# Financial Analysis Tool - Docker Update Script
# For macOS/Linux

set -e

echo ""
echo "========================================"
echo " Financial Analysis Tool - Docker Update"
echo "========================================"
echo ""

# Function to print colored output
print_info() {
    echo -e "\033[36m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

print_warning() {
    echo -e "\033[33m[WARNING]\033[0m $1"
}

print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    print_error "Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Determine docker compose command
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

print_info "Using: $DOCKER_COMPOSE"

# Navigate to the directory containing docker-compose.yml
cd "$(dirname "$0")"

print_info "Checking current container status..."
$DOCKER_COMPOSE ps

echo ""
read -p "Do you want to create a backup before updating? (y/N): " create_backup

if [[ $create_backup =~ ^[Yy]$ ]]; then
    print_info "Creating backup of persistent data..."
    
    # Create backup directory with timestamp
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Export volume data
    print_info "Backing up database and uploads..."
    docker run --rm -v financial-analysis-tool_app_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf /backup/app_data.tar.gz -C /data .
    docker run --rm -v financial-analysis-tool_app_uploads:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf /backup/app_uploads.tar.gz -C /data .
    
    print_success "Backup created in: $BACKUP_DIR"
fi

echo ""
print_info "Stopping containers..."
$DOCKER_COMPOSE down

print_info "Pulling latest images..."
$DOCKER_COMPOSE pull

print_info "Rebuilding containers..."
$DOCKER_COMPOSE build --no-cache --pull

print_info "Starting updated containers..."
$DOCKER_COMPOSE up -d

print_info "Waiting for services to be ready..."
sleep 10

# Health check
print_info "Performing health check..."
if curl -f -s http://localhost/api/status >/dev/null 2>&1; then
    print_success "Application is running successfully!"
    print_info "Access your application at:"
    echo "  HTTP:  http://localhost"
    echo "  HTTPS: https://localhost (if SSL is enabled)"
elif curl -f -s http://localhost:80/api/status >/dev/null 2>&1; then
    print_success "Application is running successfully!"
    print_info "Access your application at: http://localhost"
else
    print_warning "Application may still be starting up..."
    print_info "Check status with: $DOCKER_COMPOSE logs"
fi

echo ""
print_info "Update completed! Container logs:"
$DOCKER_COMPOSE logs --tail=20

echo ""
print_success "========================================="
print_success " Update Complete!"
print_success "========================================="
echo ""
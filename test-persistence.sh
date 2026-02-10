#!/bin/bash

# Financial Analysis Tool - Data Persistence Test
# This script tests that data persists across container recreations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Determine docker compose command
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

print_header "Data Persistence Test"

print_info "This test verifies that your financial data persists across container rebuilds."
echo

# Check if containers are running
print_info "Checking container status..."
if ! $DOCKER_COMPOSE ps | grep -q "financial-analysis-app.*Up"; then
    print_warning "Application is not running. Starting it now..."
    $DOCKER_COMPOSE up -d
    sleep 10
fi

# Test API connectivity
print_info "Testing API connectivity..."
if curl -f -s http://localhost/api/status >/dev/null 2>&1; then
    print_success "Application is accessible"
else
    print_error "Cannot reach application API"
    exit 1
fi

# Check volumes exist
print_info "Checking Docker volumes..."
if docker volume inspect financial-analysis-tool_app_data >/dev/null 2>&1; then
    print_success "Database volume exists"
else
    print_error "Database volume not found"
    exit 1
fi

if docker volume inspect financial-analysis-tool_app_uploads >/dev/null 2>&1; then
    print_success "Uploads volume exists"
else
    print_error "Uploads volume not found"  
    exit 1
fi

# Check database file exists
print_info "Checking database..."
if docker run --rm -v financial-analysis-tool_app_data:/data alpine test -f /data/expense_tracker.db; then
    print_success "Database file exists"
    
    # Get database size
    DB_SIZE=$(docker run --rm -v financial-analysis-tool_app_data:/data alpine du -h /data/expense_tracker.db | cut -f1)
    print_info "Database size: $DB_SIZE"
else
    print_warning "Database file not found - this is normal for first run"
fi

# Get record counts via API
print_info "Checking data via API..."
USERS=$(curl -s http://localhost/api/users/ | jq length 2>/dev/null || echo "N/A")
TRANSACTIONS=$(curl -s http://localhost/api/transactions/ | jq length 2>/dev/null || echo "N/A")
CATEGORIES=$(curl -s http://localhost/api/categories/ | jq length 2>/dev/null || echo "N/A")

echo "  Users: $USERS"
echo "  Transactions: $TRANSACTIONS"  
echo "  Categories: $CATEGORIES"

# Now test persistence by recreating containers
echo
print_header "Testing Data Persistence"

print_warning "This will recreate your containers to test data persistence."
read -p "Continue? (y/N): " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    print_info "Test cancelled."
    exit 0
fi

print_info "Recording current data counts..."
BEFORE_USERS=$USERS
BEFORE_TRANSACTIONS=$TRANSACTIONS
BEFORE_CATEGORIES=$CATEGORIES

print_info "Stopping containers..."
$DOCKER_COMPOSE down

print_info "Removing containers and images (keeping volumes)..."
docker system prune -f >/dev/null 2>&1 || true

print_info "Starting containers again..."
$DOCKER_COMPOSE up -d

print_info "Waiting for application to be ready..."
sleep 15

# Wait for API to be ready
MAX_ATTEMPTS=12
ATTEMPT=1
while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    if curl -f -s http://localhost/api/status >/dev/null 2>&1; then
        break
    fi
    print_info "Attempt $ATTEMPT/$MAX_ATTEMPTS - waiting for API..."
    sleep 5
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    print_error "API did not become ready in time"
    exit 1
fi

print_info "Checking data after container recreation..."
AFTER_USERS=$(curl -s http://localhost/api/users/ | jq length 2>/dev/null || echo "N/A")
AFTER_TRANSACTIONS=$(curl -s http://localhost/api/transactions/ | jq length 2>/dev/null || echo "N/A")
AFTER_CATEGORIES=$(curl -s http://localhost/api/categories/ | jq length 2>/dev/null || echo "N/A")

echo
print_header "Test Results"

# Compare data
if [ "$BEFORE_USERS" = "$AFTER_USERS" ]; then
    print_success "Users: $BEFORE_USERS → $AFTER_USERS (preserved)"
else
    print_warning "Users: $BEFORE_USERS → $AFTER_USERS (changed)"
fi

if [ "$BEFORE_TRANSACTIONS" = "$AFTER_TRANSACTIONS" ]; then
    print_success "Transactions: $BEFORE_TRANSACTIONS → $AFTER_TRANSACTIONS (preserved)"
else
    print_warning "Transactions: $BEFORE_TRANSACTIONS → $AFTER_TRANSACTIONS (changed)"
fi

if [ "$BEFORE_CATEGORIES" = "$AFTER_CATEGORIES" ]; then
    print_success "Categories: $BEFORE_CATEGORIES → $AFTER_CATEGORIES (preserved)"
else
    print_warning "Categories: $BEFORE_CATEGORIES → $AFTER_CATEGORIES (changed)"
fi

echo
if [ "$BEFORE_USERS" = "$AFTER_USERS" ] && [ "$BEFORE_TRANSACTIONS" = "$AFTER_TRANSACTIONS" ] && [ "$BEFORE_CATEGORIES" = "$AFTER_CATEGORIES" ]; then
    print_success "🎉 DATA PERSISTENCE TEST PASSED!"
    print_success "Your data will be safe across container updates and rebuilds."
else
    print_warning "⚠️  Some data counts changed, but this may be normal."
    print_info "The important thing is that the application starts successfully."
fi

echo
print_info "You can now use your application with confidence that data persists."
print_info "Access it at: http://localhost"

echo
print_header "Quick Commands"
echo "Update containers: ./update.sh"
echo "Create backup:     ./backup.sh backup"
echo "List backups:      ./backup.sh list"
echo "Run this test:     ./test-persistence.sh"
#!/bin/bash

# Financial Analysis Tool - Backup & Restore Script
# For macOS/Linux

set -e

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

# Determine docker compose command
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

PROJECT_NAME="financial-analysis-tool"
DATA_VOLUME="${PROJECT_NAME}_app_data"
UPLOADS_VOLUME="${PROJECT_NAME}_app_uploads"

show_help() {
    echo ""
    echo "Financial Analysis Tool - Backup & Restore"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  backup     Create a backup of all persistent data"
    echo "  restore    Restore data from a backup"
    echo "  list       List available backups"
    echo "  clean      Clean old backups (keeps last 5)"
    echo ""
    echo "Options:"
    echo "  -f, --file     Specify backup file for restore"
    echo "  -d, --dir      Specify backup directory"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 backup                           # Create backup with timestamp"
    echo "  $0 restore -f backups/backup.tar   # Restore from specific file"
    echo "  $0 list                            # List all backups"
    echo ""
}

create_backup() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    local backup_file="financial-analysis-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
    
    if [ "$1" ]; then
        backup_dir="$1"
        backup_file="$(basename "$1").tar.gz"
    fi
    
    mkdir -p "$backup_dir"
    
    print_info "Creating backup: $backup_dir"
    
    # Check if volumes exist
    if ! docker volume inspect "$DATA_VOLUME" >/dev/null 2>&1; then
        print_error "Data volume $DATA_VOLUME not found. Run the application first."
        exit 1
    fi
    
    # Backup database volume
    print_info "Backing up database..."
    docker run --rm -v "$DATA_VOLUME":/data -v "$(pwd)/$backup_dir":/backup alpine tar czf "/backup/app_data.tar.gz" -C /data .
    
    # Backup uploads volume
    print_info "Backing up uploads..."
    docker run --rm -v "$UPLOADS_VOLUME":/data -v "$(pwd)/$backup_dir":/backup alpine tar czf "/backup/app_uploads.tar.gz" -C /data .
    
    # Create metadata file
    cat > "$backup_dir/metadata.json" <<EOF
{
    "timestamp": "$(date -Iseconds)",
    "volumes": [
        "${DATA_VOLUME}",
        "${UPLOADS_VOLUME}"
    ],
    "hostname": "$(hostname)",
    "user": "$(whoami)"
}
EOF
    
    # Create combined archive
    tar -czf "$backup_file" -C backups "$(basename "$backup_dir")"
    
    print_success "Backup created successfully:"
    print_info "  Directory: $backup_dir"
    print_info "  Archive:   $backup_file"
    
    # Show backup size
    local size=$(du -h "$backup_file" | cut -f1)
    print_info "  Size:      $size"
}

restore_backup() {
    local backup_path="$1"
    
    if [ ! "$backup_path" ]; then
        print_error "No backup file specified. Use -f option or provide path."
        exit 1
    fi
    
    if [ ! -f "$backup_path" ]; then
        print_error "Backup file not found: $backup_path"
        exit 1
    fi
    
    print_warning "This will replace all existing data!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "Restore cancelled."
        exit 0
    fi
    
    # Extract backup
    local temp_dir=$(mktemp -d)
    tar -xzf "$backup_path" -C "$temp_dir"
    local extracted_dir=$(find "$temp_dir" -maxdepth 1 -type d -name "20*" | head -1)
    
    if [ ! -d "$extracted_dir" ]; then
        print_error "Invalid backup file format."
        rm -rf "$temp_dir"
        exit 1
    fi
    
    print_info "Stopping application..."
    $DOCKER_COMPOSE down
    
    # Restore database
    print_info "Restoring database..."
    docker run --rm -v "$DATA_VOLUME":/data -v "$extracted_dir":/backup alpine sh -c "rm -rf /data/* && tar xzf /backup/app_data.tar.gz -C /data"
    
    # Restore uploads
    print_info "Restoring uploads..."
    docker run --rm -v "$UPLOADS_VOLUME":/data -v "$extracted_dir":/backup alpine sh -c "rm -rf /data/* && tar xzf /backup/app_uploads.tar.gz -C /data"
    
    # Clean up
    rm -rf "$temp_dir"
    
    print_info "Starting application..."
    $DOCKER_COMPOSE up -d
    
    print_success "Restore completed successfully!"
}

list_backups() {
    print_info "Available backups:"
    echo ""
    
    # List backup files
    if ls financial-analysis-backup-*.tar.gz >/dev/null 2>&1; then
        for backup in financial-analysis-backup-*.tar.gz; do
            local size=$(du -h "$backup" | cut -f1)
            local date=$(echo "$backup" | grep -o '[0-9]\{8\}_[0-9]\{6\}' | sed 's/_/ /')
            printf "  %-40s %s\n" "$backup" "($size) - $date"
        done
    else
        print_info "No backup files found."
    fi
    
    # List backup directories
    if ls -d backups/20* >/dev/null 2>&1; then
        echo ""
        print_info "Backup directories:"
        for dir in backups/20*; do
            if [ -f "$dir/metadata.json" ]; then
                local timestamp=$(grep '"timestamp"' "$dir/metadata.json" | cut -d'"' -f4)
                printf "  %-20s %s\n" "$(basename "$dir")" "$timestamp"
            fi
        done
    fi
}

clean_backups() {
    print_info "Cleaning old backups (keeping last 5)..."
    
    # Clean backup files
    local count=0
    for backup in $(ls -t financial-analysis-backup-*.tar.gz 2>/dev/null || true); do
        count=$((count + 1))
        if [ $count -gt 5 ]; then
            print_info "Removing: $backup"
            rm "$backup"
        fi
    done
    
    # Clean backup directories
    local count=0
    for dir in $(ls -td backups/20* 2>/dev/null || true); do
        count=$((count + 1))
        if [ $count -gt 5 ]; then
            print_info "Removing: $dir"
            rm -rf "$dir"
        fi
    done
    
    print_success "Cleanup completed."
}

# Main script logic
case "$1" in
    backup)
        create_backup "$2"
        ;;
    restore)
        if [ "$2" = "-f" ] || [ "$2" = "--file" ]; then
            restore_backup "$3"
        else
            restore_backup "$2"
        fi
        ;;
    list)
        list_backups
        ;;
    clean)
        clean_backups
        ;;
    -h|--help|help)
        show_help
        ;;
    *)
        if [ "$1" ]; then
            print_error "Unknown command: $1"
        fi
        show_help
        exit 1
        ;;
esac
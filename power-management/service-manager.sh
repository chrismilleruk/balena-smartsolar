#!/bin/bash

# Service Lifecycle Manager for Power Optimization
# Stops non-essential services during sleep periods

LOG_FILE="/data/logs/service-mgmt.log"
COMPOSE_FILE="/usr/src/app/docker-compose.yml"

log() {
    echo "$(date -Iseconds) - $1" | tee -a "$LOG_FILE"
}

sleep_mode() {
    log "Entering sleep mode - stopping non-essential services..."
    
    # Stop services that aren't needed for data collection
    docker-compose -f "$COMPOSE_FILE" stop web cloudflared
    
    # Optionally stop telegraf if not doing real-time uploads
    # docker-compose -f "$COMPOSE_FILE" stop telegraf
    
    log "Non-essential services stopped - saving ~20mA"
}

wake_mode() {
    log "Entering wake mode - starting all services..."
    
    # Restart all services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    sleep 10
    
    log "All services started"
}

upload_mode() {
    log "Entering upload mode - ensuring upload services are running..."
    
    # Make sure upload-related services are running
    docker-compose -f "$COMPOSE_FILE" up -d telegraf
    
    log "Upload services ready"
}

case "$1" in
    sleep)
        sleep_mode
        ;;
    wake)
        wake_mode
        ;;
    upload)
        upload_mode
        ;;
    *)
        echo "Usage: $0 {sleep|wake|upload}"
        exit 1
        ;;
esac
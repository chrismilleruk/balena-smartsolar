#!/bin/bash

# WiFi Power Management for Pi Zero W
# Saves 10-20mA by disabling WiFi radio between upload cycles

WIFI_INTERFACE="wlan0"
LOG_FILE="/data/logs/power-mgmt.log"

log() {
    echo "$(date -Iseconds) - $1" | tee -a "$LOG_FILE"
}

wifi_disable() {
    log "Disabling WiFi to save power..."
    rfkill block wifi
    ip link set "$WIFI_INTERFACE" down
    log "WiFi disabled - saving ~15mA"
}

wifi_enable() {
    log "Enabling WiFi for data upload..."
    rfkill unblock wifi
    ip link set "$WIFI_INTERFACE" up
    
    # Wait for connection
    timeout=30
    while [ $timeout -gt 0 ] && ! ping -c 1 8.8.8.8 >/dev/null 2>&1; do
        sleep 1
        timeout=$((timeout - 1))
    done
    
    if [ $timeout -gt 0 ]; then
        log "WiFi connected successfully"
        return 0
    else
        log "WiFi connection failed"
        return 1
    fi
}

case "$1" in
    disable)
        wifi_disable
        ;;
    enable)
        wifi_enable
        ;;
    *)
        echo "Usage: $0 {enable|disable}"
        exit 1
        ;;
esac
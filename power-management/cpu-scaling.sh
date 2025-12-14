#!/bin/bash

# CPU Frequency Scaling for Power Optimization
# Reduces CPU frequency during idle periods to save power

LOG_FILE="/data/logs/cpu-scaling.log"
CPUFREQ_DIR="/sys/devices/system/cpu/cpu0/cpufreq"

log() {
    echo "$(date -Iseconds) - $1" | tee -a "$LOG_FILE"
}

get_available_frequencies() {
    if [ -f "$CPUFREQ_DIR/scaling_available_frequencies" ]; then
        cat "$CPUFREQ_DIR/scaling_available_frequencies"
    else
        echo "1000000 700000 600000"  # Default Pi Zero W frequencies
    fi
}

set_power_save_mode() {
    log "Setting CPU to power-save mode..."
    
    # Set governor to powersave
    echo "powersave" > "$CPUFREQ_DIR/scaling_governor" 2>/dev/null || {
        log "Could not set governor to powersave, trying ondemand"
        echo "ondemand" > "$CPUFREQ_DIR/scaling_governor" 2>/dev/null
    }
    
    # Set minimum frequency
    local freqs=$(get_available_frequencies)
    local min_freq=$(echo $freqs | tr ' ' '\n' | sort -n | head -1)
    
    echo "$min_freq" > "$CPUFREQ_DIR/scaling_min_freq" 2>/dev/null
    echo "$min_freq" > "$CPUFREQ_DIR/scaling_max_freq" 2>/dev/null
    
    local current_freq=$(cat "$CPUFREQ_DIR/scaling_cur_freq" 2>/dev/null || echo "unknown")
    log "CPU frequency set to ${current_freq}Hz - saving ~15mA"
}

set_performance_mode() {
    log "Setting CPU to performance mode..."
    
    # Set governor to performance or ondemand
    echo "ondemand" > "$CPUFREQ_DIR/scaling_governor" 2>/dev/null || {
        echo "performance" > "$CPUFREQ_DIR/scaling_governor" 2>/dev/null
    }
    
    # Set maximum frequency
    local freqs=$(get_available_frequencies)
    local max_freq=$(echo $freqs | tr ' ' '\n' | sort -n | tail -1)
    
    echo "$max_freq" > "$CPUFREQ_DIR/scaling_max_freq" 2>/dev/null
    
    local current_freq=$(cat "$CPUFREQ_DIR/scaling_cur_freq" 2>/dev/null || echo "unknown")
    log "CPU frequency restored to ${current_freq}Hz"
}

show_status() {
    echo "Current CPU frequency info:"
    echo "Governor: $(cat $CPUFREQ_DIR/scaling_governor 2>/dev/null || echo 'unavailable')"
    echo "Current: $(cat $CPUFREQ_DIR/scaling_cur_freq 2>/dev/null || echo 'unavailable')Hz"
    echo "Min: $(cat $CPUFREQ_DIR/scaling_min_freq 2>/dev/null || echo 'unavailable')Hz"
    echo "Max: $(cat $CPUFREQ_DIR/scaling_max_freq 2>/dev/null || echo 'unavailable')Hz"
    echo "Available: $(get_available_frequencies)Hz"
}

case "$1" in
    powersave)
        set_power_save_mode
        ;;
    performance)
        set_performance_mode
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {powersave|performance|status}"
        exit 1
        ;;
esac
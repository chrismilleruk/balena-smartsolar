#!/bin/sh
# Output uptime, RAM, and /data filesystem stats as JSON
# More resilient version with error handling

# Function to safely get a numeric value with fallback
get_value() {
    echo "${1:-0}" | grep -E '^[0-9]+(\.[0-9]+)?$' || echo "0"
}

# Get uptime (seconds since boot)
UPTIME=$(cut -d" " -f1 /proc/uptime 2>/dev/null | cut -d. -f1)
UPTIME=$(get_value "$UPTIME")

# Get memory stats (in bytes)
MEM_STATS=$(free -b 2>/dev/null | awk '/^Mem:/ {print $7, $2}')
if [ -n "$MEM_STATS" ]; then
    RAM_FREE=$(echo "$MEM_STATS" | awk '{print $1}')
    RAM_SIZE=$(echo "$MEM_STATS" | awk '{print $2}')
else
    RAM_FREE=0
    RAM_SIZE=0
fi
RAM_FREE=$(get_value "$RAM_FREE")
RAM_SIZE=$(get_value "$RAM_SIZE")

# Get filesystem stats for /data (in bytes)
FS_STATS=$(df -B1 /data 2>/dev/null | tail -1 | awk '{print $4, $2}')
if [ -n "$FS_STATS" ]; then
    FS_FREE=$(echo "$FS_STATS" | awk '{print $1}')
    FS_SIZE=$(echo "$FS_STATS" | awk '{print $2}')
else
    FS_FREE=0
    FS_SIZE=0
fi
FS_FREE=$(get_value "$FS_FREE")
FS_SIZE=$(get_value "$FS_SIZE")

# Get CPU temperature (convert from millidegrees to degrees)
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    CPU_TEMP_RAW=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
    if [ -n "$CPU_TEMP_RAW" ] && echo "$CPU_TEMP_RAW" | grep -qE '^[0-9]+$'; then
        CPU_TEMP=$(awk "BEGIN {printf \"%.1f\", $CPU_TEMP_RAW/1000}")
    else
        CPU_TEMP="0.0"
    fi
else
    CPU_TEMP="0.0"
fi

# Output JSON - using explicit format to ensure valid JSON
printf '{"uptime": %s, "ram_free": %s, "ram_size": %s, "fs_free": %s, "fs_size": %s, "cpu_temp": %s}\n' \
    "$UPTIME" "$RAM_FREE" "$RAM_SIZE" "$FS_FREE" "$FS_SIZE" "$CPU_TEMP"
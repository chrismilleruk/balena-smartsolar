#!/bin/sh
# Diagnostic script to check Bluetooth status and Shelly connectivity
# Run this inside the Shelly container:
# SSH directly to container: balena device ssh <device> shelly
# Run script: /usr/src/app/tests/diagnose_bluetooth.sh

SHELLY_MAC="${SHELLY_MAC:-A0:DD:6C:4B:9C:36}"

echo "=== Bluetooth Diagnostics for Shelly Service ==="
echo "Running from: $(hostname)"
echo "Date: $(date)"
echo

echo "1. Bluetooth adapter status:"
if command -v hciconfig >/dev/null 2>&1; then
    hciconfig -a
else
    echo "   hciconfig not available"
fi
echo

echo "2. Running processes:"
ps aux | grep -E "(python|bluetooth)" | grep -v grep
echo

echo "3. Python packages:"
python3 -c "import bleak; print(f'bleak version: {bleak.__version__}')" 2>/dev/null || echo "   bleak not imported"
echo

echo "4. Environment variables:"
echo "   SHELLY_MAC=$SHELLY_MAC"
echo "   SHELLY_SCAN_INTERVAL=$SHELLY_SCAN_INTERVAL"
echo

echo "5. Quick BLE scan (5 seconds):"
if command -v hcitool >/dev/null 2>&1; then
    echo "   Scanning for $SHELLY_MAC..."
    timeout 5 hcitool lescan 2>&1 | grep -i "${SHELLY_MAC}" || echo "   Device not found (this is normal if already connected)"
else
    echo "   hcitool not available"
fi
echo

echo "6. Service logs (last 20 lines):"
if [ -f /data/logs/shelly/shelly.log ]; then
    tail -20 /data/logs/shelly/shelly.log
else
    echo "   No log file found at /data/logs/shelly/shelly.log"
fi
echo

echo "7. Data collection status:"
DATA_DIR="/data/shelly-v1"
if [ -d "$DATA_DIR" ]; then
    echo "   Files in $DATA_DIR:"
    ls -la "$DATA_DIR" | tail -5
    
    TODAY_FILE="$DATA_DIR/data_$(date +%Y-%m-%d).ndjson"
    if [ -f "$TODAY_FILE" ]; then
        echo "   Last 3 entries from today:"
        tail -3 "$TODAY_FILE" | while read line; do
            echo "$line" | python3 -m json.tool 2>/dev/null || echo "$line"
        done
    else
        echo "   No data file for today"
    fi
else
    echo "   Data directory not found: $DATA_DIR"
fi
echo

echo "8. System resources:"
df -h /data
echo
free -h 2>/dev/null || echo "   free command not available"
echo

echo "=== Diagnostics complete ===" 
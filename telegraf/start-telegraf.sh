#!/bin/sh
# Wrapper script to start Telegraf with error handling

echo "Starting Telegraf..."

# Test configuration first
/usr/bin/telegraf --config /etc/telegraf/telegraf.conf --test
if [ $? -ne 0 ]; then
    echo "Configuration test failed! Keeping container running for debugging..."
    echo "To test config: telegraf --config /etc/telegraf/telegraf.conf --test"
    echo "To see available plugins: telegraf --input-list"
    # Keep container running
    tail -f /dev/null
fi

# Start Telegraf
exec /usr/bin/telegraf --config /etc/telegraf/telegraf.conf 
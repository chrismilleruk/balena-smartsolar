#!/bin/sh

# The host D-Bus is mounted at /host/run/dbus
# Environment variable DBUS_SYSTEM_BUS_ADDRESS is set in docker-compose.yml

# Start the Shelly monitoring service
echo "Starting Shelly monitoring service..."
exec python -u main.py 
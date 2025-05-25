#!/bin/sh

# The host D-Bus is mounted at /host/run/dbus
# Environment variable DBUS_SYSTEM_BUS_ADDRESS is set in docker-compose.yml

# Start the dashboard in the background
echo "Starting dashboard on port 80..."
python3 dashboard.py &

# Start the main data collection service
echo "Starting SmartSolar data collection..."
python3 main.py 
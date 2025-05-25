#!/bin/sh

echo "=== System Bluetooth Debug ==="
echo

echo "1. Checking kernel modules:"
lsmod | grep -E "bluetooth|btusb|hci" || echo "No bluetooth modules found"
echo

echo "2. Checking /dev devices:"
ls -la /dev | grep -E "hci|rfkill|tty" | head -20
echo

echo "3. Checking rfkill status:"
rfkill list || echo "rfkill not available"
echo

echo "4. Checking dmesg for bluetooth:"
dmesg | grep -i bluetooth | tail -20
echo

echo "5. Checking processes:"
ps aux | grep -E "bluetooth|dbus" | grep -v grep
echo

echo "6. Checking D-Bus status:"
if [ -S /var/run/dbus/system_bus_socket ]; then
    echo "D-Bus socket exists"
    ls -la /var/run/dbus/system_bus_socket
else
    echo "D-Bus socket not found"
fi
echo

echo "7. Checking bluetooth service:"
which bluetoothd && bluetoothd --version || echo "bluetoothd not found"
echo

echo "Debug complete!" 
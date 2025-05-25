#!/usr/bin/env python3
import asyncio
import sys
import os
from bleak import BleakScanner
import subprocess

print("=== Bluetooth Debug Script ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print()

# Check if running as root
print(f"Running as user: {os.getuid()} (0 = root)")
print()

# Check for bluetooth devices
print("Checking for Bluetooth devices in /sys/class/bluetooth/:")
try:
    devices = os.listdir("/sys/class/bluetooth/")
    print(f"Found devices: {devices}")
except Exception as e:
    print(f"Error listing bluetooth devices: {e}")
print()

# Check hciconfig
print("Running 'hciconfig -a':")
try:
    result = subprocess.run(['hciconfig', '-a'], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Errors: {result.stderr}")
except Exception as e:
    print(f"Error running hciconfig: {e}")
print()

# Check bluetoothctl
print("Running 'bluetoothctl show':")
try:
    result = subprocess.run(['bluetoothctl', 'show'], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Errors: {result.stderr}")
except Exception as e:
    print(f"Error running bluetoothctl: {e}")
print()

# Check D-Bus
print("Checking D-Bus environment:")
print(f"DBUS_SYSTEM_BUS_ADDRESS: {os.environ.get('DBUS_SYSTEM_BUS_ADDRESS', 'Not set')}")
print()

# Try to scan with bleak
print("Attempting BLE scan with bleak (10 seconds)...")
async def scan():
    try:
        devices = await BleakScanner.discover(timeout=10.0)
        print(f"Found {len(devices)} devices:")
        for device in devices:
            print(f"  - {device.name or 'Unknown'} ({device.address})")
    except Exception as e:
        print(f"Error during scan: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(scan())
print("\nDebug complete!") 
#!/usr/bin/env python3
"""
Simple Bluetooth scan to find Shelly Plus Uni
"""

import asyncio
from bleak import BleakScanner

# Updated MAC address based on scan results
SHELLY_MAC = "A0:DD:6C:4B:9C:36"

async def scan_for_shelly():
    print("Scanning for Bluetooth devices...")
    
    # Use the callback version to get advertisement data
    devices_with_data = {}
    
    def detection_callback(device, advertisement_data):
        devices_with_data[device.address] = (device, advertisement_data)
    
    scanner = BleakScanner(detection_callback=detection_callback)
    await scanner.start()
    await asyncio.sleep(10.0)  # Scan for 10 seconds
    await scanner.stop()
    
    print(f"\nFound {len(devices_with_data)} devices:")
    for address, (device, adv_data) in devices_with_data.items():
        print(f"  {device.address} - {device.name} (RSSI: {adv_data.rssi} dBm)")
        
        # Check if this is our Shelly
        if device.address.upper() == SHELLY_MAC.upper():
            print(f"\n✓ Found Shelly Plus Uni!")
            print(f"  Name: {device.name}")
            print(f"  Address: {device.address}")
            print(f"  RSSI: {adv_data.rssi} dBm")
            
            # Show additional advertisement data
            if adv_data.tx_power:
                print(f"  Tx Power: {adv_data.tx_power}")
            if adv_data.local_name:
                print(f"  Local Name: {adv_data.local_name}")
            if adv_data.service_uuids:
                print(f"  Service UUIDs: {adv_data.service_uuids}")
            if adv_data.manufacturer_data:
                print(f"  Manufacturer Data: {adv_data.manufacturer_data}")
            if adv_data.service_data:
                print(f"  Service Data: {adv_data.service_data}")
            
            return device
    
    print(f"\n✗ Shelly Plus Uni {SHELLY_MAC} not found")
    return None

if __name__ == "__main__":
    asyncio.run(scan_for_shelly()) 
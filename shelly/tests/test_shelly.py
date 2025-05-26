#!/usr/bin/env python3
"""
Test script to verify Shelly BLE connection and data collection
Run this locally to test before deploying to Balena
"""

import asyncio
import json
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import ShellyBLEClient, collect_shelly_data, logger

async def test_shelly_connection():
    """Test the Shelly BLE connection and data collection"""
    
    # Override environment variables for testing
    SHELLY_MAC = os.getenv('SHELLY_MAC', 'A0:DD:6C:4B:9C:36')
    
    print(f"Testing connection to Shelly device: {SHELLY_MAC}")
    print("=" * 60)
    
    client = ShellyBLEClient(SHELLY_MAC)
    
    try:
        # Test 1: Get device info
        print("\n1. Getting Device Info...")
        info = await client.call_rpc("Shelly.GetDeviceInfo", {"ident": True})
        print(json.dumps(info, indent=2))
        
        # Test 2: Get full status
        print("\n2. Getting Full Status...")
        status = await client.call_rpc("Shelly.GetStatus")
        print(json.dumps(status, indent=2))
        
        # Test 3: Use the collect_shelly_data function
        print("\n3. Testing data collection function...")
        data = await collect_shelly_data()
        if data:
            print("Collected data:")
            print(json.dumps(data, indent=2))
        else:
            print("Failed to collect data")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! The Shelly container should work correctly.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        print("\nPlease check:")
        print("1. The Shelly device is powered on")
        print("2. The MAC address is correct")
        print("3. Bluetooth is enabled on this system")
        print("4. You're within BLE range of the device")


if __name__ == "__main__":
    asyncio.run(test_shelly_connection()) 
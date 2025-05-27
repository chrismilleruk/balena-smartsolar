#!/usr/bin/env python3
"""
Test controlling Shelly Auto-off timer settings over Bluetooth
This allows enabling/disabling the auto-off timer which effectively
puts the device in manual mode when disabled.
"""

import asyncio
import json
import sys
import os

# Add parent directory to path to import the BLE client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shelly_ble_client import ShellyBLEClient

async def test_autooff_control():
    """Test controlling the auto-off timer via BLE"""
    
    SHELLY_MAC = os.getenv('SHELLY_MAC', 'A0:DD:6C:4B:9C:36')
    client = ShellyBLEClient(SHELLY_MAC)
    
    try:
        print(f"Connecting to Shelly device: {SHELLY_MAC}")
        print("=" * 60)
        
        # Get current switch configuration
        print("\n1. Getting current Switch configuration...")
        config = await client.call_rpc("Switch.GetConfig", {"id": 0})
        print(json.dumps(config, indent=2))
        
        if "result" in config:
            current_config = config["result"]
            auto_off = current_config.get("auto_off", False)
            auto_off_delay = current_config.get("auto_off_delay", 0)
            
            print(f"\nCurrent Auto-off setting: {'Enabled' if auto_off else 'Disabled'}")
            if auto_off:
                print(f"Auto-off delay: {auto_off_delay} seconds")
        
        # Test disabling auto-off (manual mode)
        print("\n2. Disabling Auto-off timer (entering manual mode)...")
        result = await client.call_rpc("Switch.SetConfig", {
            "id": 0,
            "config": {
                "auto_off": False
            }
        })
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Verify the change
        print("\n3. Verifying configuration change...")
        config = await client.call_rpc("Switch.GetConfig", {"id": 0})
        if "result" in config:
            auto_off = config["result"].get("auto_off", False)
            print(f"Auto-off is now: {'Enabled' if auto_off else 'Disabled'}")
        
        # Test enabling auto-off with 5 minute (300 second) delay
        print("\n4. Enabling Auto-off with 5 minute delay...")
        result = await client.call_rpc("Switch.SetConfig", {
            "id": 0,
            "config": {
                "auto_off": True,
                "auto_off_delay": 300  # 5 minutes in seconds
            }
        })
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Get final configuration
        print("\n5. Final configuration check...")
        config = await client.call_rpc("Switch.GetConfig", {"id": 0})
        print(json.dumps(config, indent=2))
        
        # Check current switch status
        print("\n6. Getting current switch status...")
        status = await client.call_rpc("Switch.GetStatus", {"id": 0})
        print(json.dumps(status, indent=2))
        
        if "result" in status:
            result = status["result"]
            print(f"\nSwitch is currently: {'ON' if result.get('output') else 'OFF'}")
            if result.get('timer_remaining'):
                print(f"Auto-off timer remaining: {result['timer_remaining']} seconds")
        
        # Test the schedule configuration
        print("\n7. Checking if device has schedules...")
        try:
            # Try to list schedules (may not be available on all devices)
            schedules = await client.call_rpc("Schedule.List")
            print(json.dumps(schedules, indent=2))
        except Exception as e:
            print(f"Schedule listing not available: {e}")
            print("(This is normal if schedules are configured via web UI)")
        
        print("\n" + "=" * 60)
        print("✅ Auto-off control test completed!")
        print("\nYou can use these RPC methods to:")
        print("- Disable auto-off to enter manual mode")
        print("- Enable auto-off with a specific delay")
        print("- Configure schedules for automatic switching")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_autooff_control()) 
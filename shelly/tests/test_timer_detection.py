#!/usr/bin/env python3
"""
Simple test to detect and monitor the auto-off countdown timer
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shelly_ble_client import ShellyBLEClient

async def monitor_timer():
    """Monitor the auto-off countdown timer"""
    
    SHELLY_MAC = os.getenv('SHELLY_MAC', 'A0:DD:6C:4B:9C:36')
    client = ShellyBLEClient(SHELLY_MAC)
    
    print("Auto-off Timer Monitor")
    print("=" * 60)
    print("Press Ctrl+C to stop\n")
    
    # Show raw response first
    print("Getting initial status (raw response)...")
    status = await client.call_rpc("Switch.GetStatus", {"id": 0})
    print(json.dumps(status, indent=2))
    print("\n" + "-" * 60 + "\n")
    
    try:
        while True:
            try:
                # Get current switch status
                status = await client.call_rpc("Switch.GetStatus", {"id": 0})
                
                if "result" in status:
                    result = status["result"]
                    output = result.get('output', False)
                    timer_started_at = result.get('timer_started_at')
                    timer_duration = result.get('timer_duration')
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    if output:
                        # Calculate remaining time from timer_started_at and timer_duration
                        if timer_started_at and timer_duration:
                            import time
                            current_time = time.time()
                            elapsed = current_time - timer_started_at
                            remaining = timer_duration - elapsed
                            
                            if remaining > 0:
                                minutes = int(remaining // 60)
                                seconds = int(remaining % 60)
                                print(f"[{timestamp}] Switch: ON | Timer: {minutes:02d}:{seconds:02d} remaining")
                            else:
                                print(f"[{timestamp}] Switch: ON | Timer: Expired (should turn off soon)")
                        else:
                            print(f"[{timestamp}] Switch: ON | Timer: Not active (manual mode)")
                    else:
                        print(f"[{timestamp}] Switch: OFF")
                        
            except Exception as e:
                print(f"Error: {e}")
                
            await asyncio.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped")

async def test_timer_scenarios():
    """Test different timer scenarios"""
    
    SHELLY_MAC = os.getenv('SHELLY_MAC', 'A0:DD:6C:4B:9C:36')
    client = ShellyBLEClient(SHELLY_MAC)
    
    print("Timer Detection Test")
    print("=" * 60)
    
    # First, show the raw response to see all available fields
    print("\n1. Getting current status (raw response)...")
    status = await client.call_rpc("Switch.GetStatus", {"id": 0})
    print(json.dumps(status, indent=2))
    
    # Scenario 1: Turn switch ON and check for timer
    print("\n2. Turning switch ON...")
    await client.call_rpc("Switch.Set", {"id": 0, "on": True})
    await asyncio.sleep(2)
    
    status = await client.call_rpc("Switch.GetStatus", {"id": 0})
    print("\nStatus after turning ON:")
    print(json.dumps(status, indent=2))
    
    if "result" in status:
        result = status["result"]
        print(f"\nAvailable fields in result: {list(result.keys())}")
        
        # Check for different possible timer fields
        timer_fields = ['timer_remaining', 'timer_started_at', 'timer_duration', 'auto_off_delay']
        for field in timer_fields:
            if field in result:
                print(f"  {field}: {result[field]}")
        
        if result.get('timer_remaining') is not None:
            print(f"\n✓ Timer detected: {result['timer_remaining']} seconds remaining")
        else:
            print("\n✗ No timer_remaining field (auto-off might be disabled)")
    
    # Scenario 2: Check if we can detect timer countdown
    print("\n2. Monitoring timer countdown for 15 seconds...")
    for i in range(3):
        await asyncio.sleep(5)
        status = await client.call_rpc("Switch.GetStatus", {"id": 0})
        if "result" in status:
            result = status["result"]
            timer = result.get('timer_remaining')
            if timer is not None:
                print(f"   Timer: {timer} seconds")
            else:
                print("   No timer active")
    
    print("\n" + "=" * 60)
    print("Test complete!")

async def reset_timer_demo():
    """Demonstrate how to reset the auto-off timer"""
    
    SHELLY_MAC = os.getenv('SHELLY_MAC', 'A0:DD:6C:4B:9C:36')
    client = ShellyBLEClient(SHELLY_MAC)
    
    print("Timer Reset Demo")
    print("=" * 60)
    print("This shows how turning ON an already-ON switch resets the timer\n")
    
    # Check initial status
    status = await client.call_rpc("Switch.GetStatus", {"id": 0})
    if "result" in status:
        result = status["result"]
        if result.get('output') and result.get('timer_started_at'):
            import time
            elapsed = time.time() - result['timer_started_at']
            remaining = result.get('timer_duration', 300) - elapsed
            print(f"Current timer: {int(remaining)}s remaining")
            
            print("\nWaiting 10 seconds...")
            await asyncio.sleep(10)
            
            print("Resetting timer by turning switch ON again...")
            await client.call_rpc("Switch.Set", {"id": 0, "on": True})
            
            # Check new status
            await asyncio.sleep(1)
            status = await client.call_rpc("Switch.GetStatus", {"id": 0})
            if "result" in status:
                result = status["result"]
                elapsed = time.time() - result['timer_started_at']
                remaining = result.get('timer_duration', 300) - elapsed
                print(f"Timer reset! New timer: {int(remaining)}s remaining")
        else:
            print("Switch is OFF or no timer active. Turn it ON first.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "monitor":
            # Run continuous monitoring
            asyncio.run(monitor_timer())
        elif sys.argv[1] == "reset":
            # Demo timer reset
            asyncio.run(reset_timer_demo())
    else:
        # Run test scenarios
        asyncio.run(test_timer_scenarios()) 
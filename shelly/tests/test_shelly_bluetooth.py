#!/usr/bin/env python3
"""
Simple test script to connect to Shelly Plus Uni over Bluetooth
and read battery voltage, output states, and network status
"""

import asyncio
import json
from bleak import BleakClient, BleakScanner
import struct
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shelly Plus Uni MAC address from scan results
SHELLY_MAC = "A0:DD:6C:4B:9C:36"

# Shelly BLE RPC Service and Characteristic UUIDs
SHELLY_SERVICE_UUID = "5f6d4f53-5f52-5043-5f53-56435f49445f"
SHELLY_DATA_CHAR_UUID = "5f6d4f53-5f52-5043-5f64-6174615f5f5f"
SHELLY_TX_CTL_CHAR_UUID = "5f6d4f53-5f52-5043-5f74-785f63746c5f"
SHELLY_RX_CTL_CHAR_UUID = "5f6d4f53-5f52-5043-5f72-785f63746c5f"

class ShellyBLEClient:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.client = None
        self.response_data = bytearray()
        self.response_complete = asyncio.Event()
        
    async def notification_handler(self, sender, data):
        """Handle incoming data from Shelly"""
        logger.debug(f"Received data: {data.hex()}")
        self.response_data.extend(data)
        
        # Check if we have a complete response (simple check for now)
        try:
            # Try to decode as JSON to see if complete
            response_str = self.response_data.decode('utf-8')
            json.loads(response_str)
            self.response_complete.set()
        except:
            # Not complete yet, wait for more data
            pass
    
    async def connect(self):
        """Connect to Shelly device"""
        logger.info(f"Scanning for Shelly Plus Uni {self.mac_address}...")
        
        device = await BleakScanner.find_device_by_address(
            self.mac_address,
            timeout=10.0
        )
        
        if not device:
            raise Exception(f"Could not find device {self.mac_address}")
            
        logger.info(f"Found device: {device.name}")
        
        self.client = BleakClient(device)
        await self.client.connect()
        logger.info("Connected!")
        
        # Subscribe to notifications
        await self.client.start_notify(SHELLY_DATA_CHAR_UUID, self.notification_handler)
        
    async def send_rpc_command(self, method, params=None):
        """Send RPC command to Shelly"""
        # Clear previous response
        self.response_data = bytearray()
        self.response_complete.clear()
        
        # Build RPC request
        request = {
            "id": 1,
            "method": method
        }
        if params:
            request["params"] = params
            
        request_json = json.dumps(request)
        request_bytes = request_json.encode('utf-8')
        
        logger.info(f"Sending RPC: {method}")
        logger.debug(f"Request: {request_json}")
        
        # Send the request
        # Shelly expects the length first (2 bytes, little endian)
        length_bytes = struct.pack('<H', len(request_bytes))
        await self.client.write_gatt_char(
            SHELLY_TX_CTL_CHAR_UUID, 
            length_bytes,
            response=True
        )
        
        # Send the actual data in chunks if needed
        chunk_size = 20  # BLE MTU limitation
        for i in range(0, len(request_bytes), chunk_size):
            chunk = request_bytes[i:i+chunk_size]
            await self.client.write_gatt_char(
                SHELLY_DATA_CHAR_UUID,
                chunk,
                response=False
            )
            
        # Wait for response
        try:
            await asyncio.wait_for(self.response_complete.wait(), timeout=5.0)
            response_str = self.response_data.decode('utf-8')
            return json.loads(response_str)
        except asyncio.TimeoutError:
            logger.error("Response timeout")
            return None
            
    async def disconnect(self):
        """Disconnect from device"""
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected")

async def test_shelly_bluetooth():
    """Test basic Shelly Plus Uni functionality over Bluetooth"""
    
    shelly = ShellyBLEClient(SHELLY_MAC)
    
    try:
        # Connect to device
        await shelly.connect()
        
        # 1. Get device info and status
        logger.info("\n=== Getting Device Status ===")
        status = await shelly.send_rpc_command("Shelly.GetStatus")
        if status:
            logger.info(f"Device Status: {json.dumps(status, indent=2)}")
            
            # Extract key information
            if "result" in status:
                result = status["result"]
                
                # Check WiFi status
                if "wifi" in result:
                    wifi_status = result["wifi"]["sta_ip"] is not None
                    logger.info(f"WiFi Connected: {wifi_status}")
                    if wifi_status:
                        logger.info(f"WiFi IP: {result['wifi']['sta_ip']}")
                
                # Check voltage (voltmeter)
                if "voltmeter:100" in result:
                    voltage = result["voltmeter:100"]["voltage"]
                    logger.info(f"Battery 2 Voltage: {voltage}V")
                
                # Check switch states
                for i in range(2):
                    switch_key = f"switch:{i}"
                    if switch_key in result:
                        switch_data = result[switch_key]
                        logger.info(f"Output {i+1} (OUT{i+1}): {'ON' if switch_data['output'] else 'OFF'}")
                        if "apower" in switch_data:
                            logger.info(f"  Power: {switch_data['apower']}W")
        
        # 2. Test controlling outputs
        logger.info("\n=== Testing Output Control ===")
        
        # Turn OUT1 on
        logger.info("Turning OUT1 ON...")
        result = await shelly.send_rpc_command("Switch.Set", {"id": 0, "on": True})
        if result:
            logger.info(f"OUT1 turned ON: {result}")
        
        await asyncio.sleep(2)
        
        # Turn OUT1 off
        logger.info("Turning OUT1 OFF...")
        result = await shelly.send_rpc_command("Switch.Set", {"id": 0, "on": False})
        if result:
            logger.info(f"OUT1 turned OFF: {result}")
            
        # 3. Get specific component status
        logger.info("\n=== Getting Voltmeter Status ===")
        voltmeter = await shelly.send_rpc_command("Voltmeter.GetStatus", {"id": 100})
        if voltmeter and "result" in voltmeter:
            logger.info(f"Voltmeter reading: {voltmeter['result']['voltage']}V")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        
    finally:
        await shelly.disconnect()

if __name__ == "__main__":
    asyncio.run(test_shelly_bluetooth()) 
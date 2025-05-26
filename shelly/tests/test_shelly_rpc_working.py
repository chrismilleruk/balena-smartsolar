#!/usr/bin/env python3
"""
Working RPC test for Shelly Plus Uni over Bluetooth
"""

import asyncio
import json
from bleak import BleakClient, BleakScanner
import struct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SHELLY_MAC = "A0:DD:6C:4B:9C:36"

# Confirmed UUIDs from discovery
SHELLY_SERVICE_UUID = "5f6d4f53-5f52-5043-5f53-56435f49445f"
SHELLY_DATA_CHAR_UUID = "5f6d4f53-5f52-5043-5f64-6174615f5f5f"  # read/write
SHELLY_TX_CTL_CHAR_UUID = "5f6d4f53-5f52-5043-5f74-785f63746c5f"  # write only
SHELLY_RX_CTL_CHAR_UUID = "5f6d4f53-5f52-5043-5f72-785f63746c5f"  # read/notify/indicate

class ShellyBLEClient:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.client = None
        self.response_data = bytearray()
        self.response_complete = asyncio.Event()
        
    async def notification_handler(self, sender, data):
        """Handle incoming data from Shelly"""
        logger.debug(f"Notification from {sender}: {data.hex()}")
        
        # First 4 bytes might be a header/length indicator
        if len(data) >= 4 and len(self.response_data) == 0:
            # This might be the RX control notification with length
            length = struct.unpack('<I', data)[0]
            logger.debug(f"Expected response length: {length}")
        else:
            # This is actual data
            self.response_data.extend(data)
            
            # Try to parse as JSON to check if complete
            try:
                response_str = self.response_data.decode('utf-8')
                json.loads(response_str)
                logger.debug("Complete JSON response received")
                self.response_complete.set()
            except:
                # Not complete yet
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
        
        # Subscribe to notifications on RX control characteristic
        await self.client.start_notify(SHELLY_RX_CTL_CHAR_UUID, self.notification_handler)
        logger.info("Subscribed to notifications")
        
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
        logger.debug(f"Request length: {len(request_bytes)} bytes")
        
        try:
            # Write the length to TX control (4 bytes, little endian)
            length_bytes = struct.pack('<I', len(request_bytes))
            await self.client.write_gatt_char(
                SHELLY_TX_CTL_CHAR_UUID, 
                length_bytes,
                response=False  # Try without response
            )
            logger.debug(f"Sent length: {length_bytes.hex()}")
            
            # Small delay
            await asyncio.sleep(0.1)
            
            # Write the actual data
            await self.client.write_gatt_char(
                SHELLY_DATA_CHAR_UUID,
                request_bytes,
                response=False
            )
            logger.debug("Sent data")
            
            # Wait for response
            try:
                await asyncio.wait_for(self.response_complete.wait(), timeout=5.0)
                response_str = self.response_data.decode('utf-8')
                logger.debug(f"Response: {response_str}")
                return json.loads(response_str)
            except asyncio.TimeoutError:
                logger.error("Response timeout")
                # Try reading the data characteristic directly
                try:
                    data = await self.client.read_gatt_char(SHELLY_DATA_CHAR_UUID)
                    logger.info(f"Direct read result: {data}")
                except Exception as e:
                    logger.error(f"Direct read failed: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return None
            
    async def disconnect(self):
        """Disconnect from device"""
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected")

async def test_shelly_rpc():
    """Test basic Shelly Plus Uni functionality over Bluetooth"""
    
    shelly = ShellyBLEClient(SHELLY_MAC)
    
    try:
        # Connect to device
        await shelly.connect()
        
        # Try a simple command first
        logger.info("\n=== Testing RPC Communication ===")
        
        # Get device info
        result = await shelly.send_rpc_command("Shelly.GetDeviceInfo")
        if result:
            logger.info(f"Device Info: {json.dumps(result, indent=2)}")
        
        # If that doesn't work, try GetStatus
        if not result:
            logger.info("\nTrying Shelly.GetStatus...")
            result = await shelly.send_rpc_command("Shelly.GetStatus")
            if result:
                logger.info(f"Status: {json.dumps(result, indent=2)}")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await shelly.disconnect()

if __name__ == "__main__":
    asyncio.run(test_shelly_rpc()) 
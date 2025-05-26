#!/usr/bin/env python3
"""
Focused test to understand Shelly BLE RPC protocol
"""

import asyncio
import json
from bleak import BleakClient, BleakScanner
import struct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SHELLY_MAC = "A0:DD:6C:4B:9C:36"

# Confirmed UUIDs
SHELLY_DATA_CHAR_UUID = "5f6d4f53-5f52-5043-5f64-6174615f5f5f"  # read/write
SHELLY_TX_CTL_CHAR_UUID = "5f6d4f53-5f52-5043-5f74-785f63746c5f"  # write only
SHELLY_RX_CTL_CHAR_UUID = "5f6d4f53-5f52-5043-5f72-785f63746c5f"  # read/notify/indicate

class ShellyBLEClient:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.client = None
        self.rx_data = bytearray()
        self.response_ready = asyncio.Event()
        
    async def rx_notification_handler(self, sender, data):
        """Handle RX control notifications"""
        logger.info(f"📥 RX notification: {data.hex()}")
        
        if len(data) == 4:
            # This might be a length indicator
            length = struct.unpack('<I', data)[0]
            logger.info(f"   Possible length indicator: {length} bytes")
            if length > 0:
                self.rx_data = bytearray()  # Reset buffer
                self.expected_length = length
            else:
                # Length 0 might mean ready for next command
                self.response_ready.set()
        
    async def data_notification_handler(self, sender, data):
        """Handle data characteristic notifications"""
        logger.info(f"📥 Data notification: {data.hex()}")
        logger.info(f"   As string: {data.decode('utf-8', errors='ignore')}")
        
        self.rx_data.extend(data)
        
        # Check if we have a complete JSON response
        try:
            json.loads(self.rx_data.decode('utf-8'))
            logger.info("✅ Complete JSON response received!")
            self.response_ready.set()
        except:
            pass
    
    async def connect(self):
        """Connect to Shelly device"""
        logger.info(f"Connecting to {self.mac_address}...")
        
        device = await BleakScanner.find_device_by_address(self.mac_address, timeout=10.0)
        if not device:
            raise Exception(f"Device not found")
            
        self.client = BleakClient(device)
        await self.client.connect()
        logger.info("Connected!")
        
        # Subscribe to both characteristics
        await self.client.start_notify(SHELLY_RX_CTL_CHAR_UUID, self.rx_notification_handler)
        
        # Try to subscribe to data characteristic too
        try:
            await self.client.start_notify(SHELLY_DATA_CHAR_UUID, self.data_notification_handler)
            logger.info("Subscribed to both RX control and Data notifications")
        except:
            logger.info("Could not subscribe to Data characteristic (might not support notify)")
        
    async def send_rpc_command(self, method, params=None):
        """Send RPC command using the protocol we discovered"""
        self.rx_data = bytearray()
        self.response_ready.clear()
        
        # Build request
        request = {"id": 1, "method": method}
        if params:
            request["params"] = params
            
        request_json = json.dumps(request)
        request_bytes = request_json.encode('utf-8')
        
        logger.info(f"\n📤 Sending: {method}")
        logger.info(f"   JSON: {request_json}")
        logger.info(f"   Length: {len(request_bytes)} bytes")
        
        try:
            # Step 1: Write length to TX control (4 bytes, little endian)
            length_bytes = struct.pack('<I', len(request_bytes))
            await self.client.write_gatt_char(SHELLY_TX_CTL_CHAR_UUID, length_bytes, response=False)
            logger.info(f"   Sent length to TX control: {length_bytes.hex()}")
            
            await asyncio.sleep(0.1)
            
            # Step 2: Write data
            await self.client.write_gatt_char(SHELLY_DATA_CHAR_UUID, request_bytes, response=False)
            logger.info(f"   Sent data")
            
            # Wait for response
            await asyncio.sleep(0.5)
            
            # Try reading data characteristic
            try:
                data = await self.client.read_gatt_char(SHELLY_DATA_CHAR_UUID)
                if data and len(data) > 0:
                    logger.info(f"📥 Data read: {data.hex()}")
                    logger.info(f"   As string: {data.decode('utf-8', errors='ignore')}")
                    try:
                        response = json.loads(data.decode('utf-8'))
                        return response
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Could not read data: {e}")
            
            # Check if we got data via notifications
            if self.rx_data:
                try:
                    response = json.loads(self.rx_data.decode('utf-8'))
                    return response
                except:
                    logger.info(f"Incomplete response: {self.rx_data}")
                    
        except Exception as e:
            logger.error(f"Error: {e}")
            
        return None
            
    async def disconnect(self):
        if self.client:
            await self.client.disconnect()

async def test_shelly_protocol():
    """Test Shelly BLE RPC protocol"""
    
    shelly = ShellyBLEClient(SHELLY_MAC)
    
    try:
        await shelly.connect()
        
        # Test 1: Simple command
        logger.info("\n=== Test 1: Shelly.GetDeviceInfo ===")
        result = await shelly.send_rpc_command("Shelly.GetDeviceInfo")
        if result:
            logger.info(f"✅ Response: {json.dumps(result, indent=2)}")
        
        # Test 2: Get status
        logger.info("\n=== Test 2: Shelly.GetStatus ===")
        result = await shelly.send_rpc_command("Shelly.GetStatus")
        if result:
            logger.info(f"✅ Response: {json.dumps(result, indent=2)}")
            
            # Extract key info if successful
            if "result" in result:
                r = result["result"]
                
                # Check for voltmeter
                if "voltmeter:100" in r:
                    voltage = r["voltmeter:100"].get("voltage", "N/A")
                    logger.info(f"\n🔋 Battery 2 Voltage: {voltage}V")
                
                # Check switches
                for i in range(2):
                    key = f"switch:{i}"
                    if key in r:
                        state = "ON" if r[key]["output"] else "OFF"
                        logger.info(f"🔌 Output {i+1}: {state}")
        
        # Test 3: Try controlling a switch
        logger.info("\n=== Test 3: Control Switch ===")
        result = await shelly.send_rpc_command("Switch.Set", {"id": 0, "on": True})
        if result:
            logger.info(f"✅ Switch control response: {json.dumps(result, indent=2)}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await shelly.disconnect()

if __name__ == "__main__":
    asyncio.run(test_shelly_protocol()) 
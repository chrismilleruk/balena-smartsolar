#!/usr/bin/env python3
"""
Debug version to understand Shelly BLE protocol
"""

import asyncio
import json
from bleak import BleakClient, BleakScanner
import struct
import logging

logging.basicConfig(level=logging.DEBUG)
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
        self.all_notifications = []
        
    async def notification_handler(self, sender, data):
        """Handle incoming data from Shelly"""
        logger.info(f"📥 Notification from {sender}: {data.hex()}")
        logger.info(f"   Raw bytes: {data}")
        logger.info(f"   Length: {len(data)}")
        
        self.all_notifications.append(data)
        
        # Try different interpretations
        if len(data) >= 4:
            # Try as little endian uint32
            val_le = struct.unpack('<I', data[:4])[0]
            logger.info(f"   As uint32 LE: {val_le}")
            
            # Try as big endian uint32
            val_be = struct.unpack('>I', data[:4])[0]
            logger.info(f"   As uint32 BE: {val_be}")
        
        # Try to decode as string
        try:
            text = data.decode('utf-8')
            logger.info(f"   As string: {text}")
        except:
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
        
    async def test_different_formats(self):
        """Try different command formats"""
        
        # Test 1: Simple string write to data characteristic
        logger.info("\n🧪 Test 1: Simple string write to data")
        try:
            test_cmd = '{"id":1,"method":"Shelly.GetDeviceInfo"}'
            await self.client.write_gatt_char(SHELLY_DATA_CHAR_UUID, test_cmd.encode(), response=False)
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Test 1 failed: {e}")
        
        # Test 2: Write length as 2 bytes instead of 4
        logger.info("\n🧪 Test 2: Length as 2 bytes (uint16)")
        try:
            test_cmd = '{"id":1,"method":"Shelly.GetStatus"}'
            length = struct.pack('<H', len(test_cmd))  # 2 bytes
            await self.client.write_gatt_char(SHELLY_TX_CTL_CHAR_UUID, length, response=False)
            await asyncio.sleep(0.1)
            await self.client.write_gatt_char(SHELLY_DATA_CHAR_UUID, test_cmd.encode(), response=False)
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Test 2 failed: {e}")
        
        # Test 3: Write everything to TX control
        logger.info("\n🧪 Test 3: Everything to TX control")
        try:
            test_cmd = '{"id":1,"method":"Shelly.GetDeviceInfo"}'
            await self.client.write_gatt_char(SHELLY_TX_CTL_CHAR_UUID, test_cmd.encode(), response=False)
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Test 3 failed: {e}")
        
        # Test 4: Try reading RX control after writing
        logger.info("\n🧪 Test 4: Read RX control after command")
        try:
            test_cmd = '{"id":1,"method":"Shelly.GetStatus"}'
            await self.client.write_gatt_char(SHELLY_DATA_CHAR_UUID, test_cmd.encode(), response=False)
            await asyncio.sleep(0.5)
            
            # Try reading
            rx_data = await self.client.read_gatt_char(SHELLY_RX_CTL_CHAR_UUID)
            logger.info(f"RX Control read: {rx_data.hex()} - {rx_data}")
        except Exception as e:
            logger.error(f"Test 4 failed: {e}")
        
        # Test 5: Check if we need to enable notifications differently
        logger.info("\n🧪 Test 5: Re-subscribe with indicate")
        try:
            await self.client.stop_notify(SHELLY_RX_CTL_CHAR_UUID)
            await asyncio.sleep(0.5)
            await self.client.start_notify(SHELLY_RX_CTL_CHAR_UUID, self.notification_handler)
            
            # Send a command
            test_cmd = '{"id":1,"method":"Shelly.GetDeviceInfo"}'
            length = struct.pack('<I', len(test_cmd))
            await self.client.write_gatt_char(SHELLY_TX_CTL_CHAR_UUID, length, response=False)
            await asyncio.sleep(0.1)
            await self.client.write_gatt_char(SHELLY_DATA_CHAR_UUID, test_cmd.encode(), response=False)
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Test 5 failed: {e}")
            
    async def disconnect(self):
        """Disconnect from device"""
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected")

async def test_shelly_debug():
    """Debug Shelly BLE protocol"""
    
    shelly = ShellyBLEClient(SHELLY_MAC)
    
    try:
        await shelly.connect()
        await shelly.test_different_formats()
        
        logger.info(f"\n📊 Total notifications received: {len(shelly.all_notifications)}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await shelly.disconnect()

if __name__ == "__main__":
    asyncio.run(test_shelly_debug()) 
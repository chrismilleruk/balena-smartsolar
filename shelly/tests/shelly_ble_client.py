#!/usr/bin/env python3
"""
Simplified Shelly BLE client for reading battery voltage and controlling outputs
Based on the official Shelly BLE RPC protocol
"""

import asyncio
import json
import struct
import random
import logging
from typing import Any, Dict, Optional, Tuple
from bleak import BleakClient, BleakScanner

# Shelly BLE Service and Characteristic UUIDs
SHELLY_SERVICE_UUID = "5f6d4f53-5f52-5043-5f53-56435f49445f"
RPC_CHAR_DATA_UUID = "5f6d4f53-5f52-5043-5f64-6174615f5f5f"
RPC_CHAR_TX_CTL_UUID = "5f6d4f53-5f52-5043-5f74-785f63746c5f"
RPC_CHAR_RX_CTL_UUID = "5f6d4f53-5f52-5043-5f72-785f63746c5f"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShellyBLEClient:
    """Simplified Shelly BLE client for RPC communication"""
    
    def __init__(self, mac_address: str):
        self.mac_address = mac_address
        self.client = None
        
    async def call_rpc(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """Execute an RPC call to the Shelly device"""
        
        async with BleakClient(self.mac_address) as client:
            if not client.is_connected:
                raise Exception(f"Failed to connect to {self.mac_address}")
                
            logger.info(f"Connected to {self.mac_address}")
            
            # Get the Shelly service
            services = client.services
            shelly_service = services.get_service(SHELLY_SERVICE_UUID)
            if not shelly_service:
                raise Exception("Shelly service not found")
                
            # Get characteristics
            data_char = shelly_service.get_characteristic(RPC_CHAR_DATA_UUID)
            tx_ctl_char = shelly_service.get_characteristic(RPC_CHAR_TX_CTL_UUID)
            rx_ctl_char = shelly_service.get_characteristic(RPC_CHAR_RX_CTL_UUID)
            
            if not all([data_char, tx_ctl_char, rx_ctl_char]):
                raise Exception("Required characteristics not found")
                
            # Prepare RPC request
            request_id = random.randint(1, 1_000_000_000)
            rpc_request = {
                "id": request_id,
                "src": "user_1",
                "method": method
            }
            if params:
                rpc_request["params"] = params
                
            rpc_json = json.dumps(rpc_request)
            rpc_bytes = rpc_json.encode("utf-8")
            rpc_length = len(rpc_bytes)
            
            logger.debug(f"RPC Request: {rpc_json}")
            
            # Send length to TX control characteristic (big-endian 4 bytes)
            length_bytes = struct.pack(">I", rpc_length)
            await client.write_gatt_char(tx_ctl_char, length_bytes, response=True)
            logger.debug(f"Sent length: {rpc_length} bytes")
            
            # Send RPC request to data characteristic
            await client.write_gatt_char(data_char, rpc_bytes, response=True)
            logger.debug("Sent RPC request")
            
            # Read expected response length from RX control characteristic
            rx_length_bytes = await client.read_gatt_char(rx_ctl_char)
            response_length = struct.unpack(">I", rx_length_bytes)[0]
            logger.debug(f"Expected response length: {response_length} bytes")
            
            # Read response data in chunks
            response_data = bytearray()
            bytes_remaining = response_length
            
            while bytes_remaining > 0:
                chunk = await client.read_gatt_char(data_char)
                response_data.extend(chunk)
                bytes_remaining -= len(chunk)
                logger.debug(f"Read {len(chunk)} bytes, {bytes_remaining} remaining")
                
            # Parse response
            response_json = response_data.decode("utf-8")
            response = json.loads(response_json)
            logger.debug(f"Response: {response_json}")
            
            # Validate response
            if response.get("id") != request_id:
                raise Exception("Response ID mismatch")
                
            if "error" in response:
                raise Exception(f"RPC Error: {response['error']}")
                
            return response


async def test_shelly():
    """Test the Shelly BLE client"""
    
    # Your Shelly Plus Uni MAC address
    SHELLY_MAC = "A0:DD:6C:4B:9C:36"
    
    client = ShellyBLEClient(SHELLY_MAC)
    
    try:
        # Get device info
        print("\n=== Getting Device Info ===")
        info = await client.call_rpc("Shelly.GetDeviceInfo", {"ident": True})
        print(json.dumps(info, indent=2))
        
        # Get status (includes input states)
        print("\n=== Getting Status ===")
        status = await client.call_rpc("Shelly.GetStatus")
        print(json.dumps(status, indent=2))
        
        # The analog input voltage should be in the status
        if "result" in status:
            result = status["result"]
            
            # Look for input voltages
            if "input:0" in result:
                input0 = result["input:0"]
                if "voltage" in input0:
                    print(f"\nBattery 2 Voltage: {input0['voltage']}V")
                    
            # Look for switch states
            if "switch:0" in result:
                switch0 = result["switch:0"]
                print(f"\nSwitch 0 (WiFi Power): {'ON' if switch0.get('output') else 'OFF'}")
                
        # Get configuration
        print("\n=== Getting Config ===")
        config = await client.call_rpc("Shelly.GetConfig")
        print(json.dumps(config, indent=2))
        
        # Example: Toggle switch 0 (WiFi power)
        # print("\n=== Toggling Switch 0 ===")
        # toggle_result = await client.call_rpc("Switch.Toggle", {"id": 0})
        # print(json.dumps(toggle_result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_shelly()) 
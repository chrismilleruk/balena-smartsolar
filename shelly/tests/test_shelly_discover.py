#!/usr/bin/env python3
"""
Discover services and characteristics on Shelly Plus Uni
"""

import asyncio
from bleak import BleakClient, BleakScanner
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SHELLY_MAC = "A0:DD:6C:4B:9C:36"

async def discover_shelly_services():
    """Discover all services and characteristics"""
    
    logger.info(f"Scanning for Shelly Plus Uni {SHELLY_MAC}...")
    device = await BleakScanner.find_device_by_address(SHELLY_MAC, timeout=10.0)
    
    if not device:
        logger.error(f"Could not find device {SHELLY_MAC}")
        return
        
    logger.info(f"Found device: {device.name}")
    
    async with BleakClient(device) as client:
        logger.info("Connected!")
        
        # Get all services using the services property
        services = client.services
        
        logger.info(f"\nDiscovered services:")
        
        for service in services:
            logger.info(f"\nService: {service.uuid}")
            logger.info(f"  Handle: {service.handle}")
            
            # Get characteristics for this service
            for char in service.characteristics:
                properties = ", ".join(char.properties)
                logger.info(f"\n  Characteristic: {char.uuid}")
                logger.info(f"    Handle: {char.handle}")
                logger.info(f"    Properties: {properties}")
                
                # Try to read if readable
                if "read" in char.properties:
                    try:
                        value = await client.read_gatt_char(char.uuid)
                        logger.info(f"    Value (hex): {value.hex()}")
                        logger.info(f"    Value (bytes): {value}")
                        # Try to decode as string if possible
                        try:
                            logger.info(f"    Value (string): {value.decode('utf-8')}")
                        except:
                            pass
                    except Exception as e:
                        logger.info(f"    Could not read: {e}")
                
                # List descriptors
                for descriptor in char.descriptors:
                    logger.info(f"    Descriptor: {descriptor.uuid}")
                    try:
                        desc_value = await client.read_gatt_descriptor(descriptor.handle)
                        logger.info(f"      Value: {desc_value.hex()}")
                    except Exception as e:
                        logger.info(f"      Could not read: {e}")

if __name__ == "__main__":
    asyncio.run(discover_shelly_services()) 
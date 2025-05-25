#!/usr/bin/env python3
"""
Debug tool for testing Victron BLE data collection.
This script helps verify that encryption keys are working and data is being parsed correctly.
"""
import asyncio
import logging
from bleak import BleakScanner
from victron_ble.devices import detect_device_type
import json
from datetime import datetime
import os
from key_manager import load_device_keys, parse_victron_data

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = "/data/smartsolar-v1"
os.makedirs(DATA_DIR, exist_ok=True)

# Load device keys
DEVICE_KEYS = load_device_keys()

# If a specific device is provided via environment variable, use it
TARGET_DEVICE = os.environ.get('SMARTSOLAR_TARGET_DEVICE', None)

def save_parsed_data(parsed_data, device_name, device_address):
    """Save parsed data to JSON file."""
    try:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        json_file = os.path.join(DATA_DIR, f"debug_data_{date_str}.json")
        
        data_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "device_name": device_name,
            "device_address": device_address,
            "parsed_data": parsed_data
        }
        
        # Read existing data if file exists
        existing_data = []
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                pass
        
        # Append new data
        existing_data.append(data_entry)
        
        # Write back to file
        with open(json_file, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        logger.info(f"Debug data saved to {json_file}")
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")

def detection_callback(device, advertisement_data):
    """Callback for when a device is detected."""
    # If target device is specified, only process that one
    if TARGET_DEVICE and device.address != TARGET_DEVICE:
        return
    
    # Check if we have a key for this device
    encryption_key = DEVICE_KEYS.get(device.address)
    if not encryption_key:
        # Only log once per device
        if not hasattr(detection_callback, 'logged_devices'):
            detection_callback.logged_devices = set()
        if device.address not in detection_callback.logged_devices:
            logger.warning(f"No encryption key found for device: {device.name} ({device.address})")
            detection_callback.logged_devices.add(device.address)
        return
    
    logger.info(f"Found device with key: {device.name} ({device.address})")
    logger.debug(f"Advertisement data: {advertisement_data}")
    
    # Check for manufacturer data
    if advertisement_data.manufacturer_data:
        for mfr_id, data in advertisement_data.manufacturer_data.items():
            logger.debug(f"Manufacturer ID: {mfr_id} (hex: {hex(mfr_id)})")
            logger.debug(f"Raw data: {data.hex()}")
            
            # Check if this is Victron data
            if mfr_id == 737:  # 0x02E1
                try:
                    # Detect device type and parse
                    parser_class = detect_device_type(data)
                    if parser_class:
                        logger.info(f"Detected device type: {parser_class.__name__}")
                        parser = parser_class(encryption_key)
                        parsed = parser.parse(data)
                        
                        # Convert to dictionary using shared function
                        parsed_dict = parse_victron_data(parsed)
                        
                        logger.info(f"Parsed data: {parsed_dict}")
                        
                        # Save the parsed data
                        save_parsed_data(parsed_dict, device.name, device.address)
                    else:
                        logger.warning("Could not detect device type")
                except Exception as e:
                    logger.error(f"Error parsing data: {e}")

async def main():
    """Main function to scan for devices."""
    if not DEVICE_KEYS:
        logger.error("No device encryption keys configured!")
        logger.error("Please add keys via the web UI or set environment variables")
        logger.error("Format: SMARTSOLAR_KEY_XX_XX_XX_XX_XX_XX=your_key_here")
        return
    
    logger.info(f"Starting Victron BLE debug reader with {len(DEVICE_KEYS)} configured device(s)")
    if TARGET_DEVICE:
        logger.info(f"Targeting specific device: {TARGET_DEVICE}")
    logger.info("Listening for advertisements...")
    logger.info("Debug data will be saved to /data/smartsolar-v1/debug_data_*.json")
    
    scanner = BleakScanner(detection_callback=detection_callback)
    
    while True:
        try:
            # Scan for 30 seconds
            await scanner.start()
            await asyncio.sleep(30)
            await scanner.stop()
            
            # Wait before next scan
            logger.info("Waiting before next scan...")
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Scanner error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main()) 
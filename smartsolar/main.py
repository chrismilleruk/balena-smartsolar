import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from bleak import BleakScanner, BleakClient
import json
from datetime import datetime, timezone
import os
import sys
from victron_ble.devices import detect_device_type
from key_manager import load_device_keys, parse_victron_data

# Constants
VERSION = "v1"
SLUG = "smartsolar"
DATA_DIR = f"/data/{SLUG}-{VERSION}"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Configure logging
def setup_logging():
    log_file = os.path.join(DATA_DIR, "smartsolar.log")
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create and configure file handler with daily rotation for warnings/errors
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(logging.WARNING)  # Only warnings and errors to file
    
    # Console handler for info and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)  # Info and above to console
    
    # Configure root logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Changed to DEBUG to see more details
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# Configurable timing via environment variables (after logger is available)
def get_config():
    """Load and validate configuration from environment variables."""
    ble_scan_timeout = int(os.getenv('BLE_SCAN_TIMEOUT', '5'))
    collection_interval = int(os.getenv('COLLECTION_INTERVAL', '60'))
    
    # Validate BLE scan timeout
    if ble_scan_timeout < 1:
        logger.warning(f"BLE_SCAN_TIMEOUT too low ({ble_scan_timeout}), setting to 1 second")
        ble_scan_timeout = 1
    elif ble_scan_timeout > 30:
        logger.warning(f"BLE_SCAN_TIMEOUT too high ({ble_scan_timeout}), setting to 30 seconds")
        ble_scan_timeout = 30
    
    # Validate collection interval
    if collection_interval < 10:
        logger.warning(f"COLLECTION_INTERVAL too low ({collection_interval}), setting to 10 seconds")
        collection_interval = 10
    
    return ble_scan_timeout, collection_interval

# Load configuration
BLE_SCAN_TIMEOUT, COLLECTION_INTERVAL = get_config()

# Device keys will be loaded dynamically
DEVICE_KEYS = {}

# Global variable to store discovered devices with their data
discovered_devices = {}

def detection_callback(device, advertisement_data):
    """Callback for when a device is detected during scanning."""
    if device.name and ("SmartSolar" in device.name or "Victron" in device.name):
        logger.debug(f"Found Victron device in callback: {device.name} ({device.address})")
        
        # Check for manufacturer data
        if advertisement_data.manufacturer_data:
            for mfr_id, data in advertisement_data.manufacturer_data.items():
                if mfr_id == 737:  # Victron manufacturer ID (0x02E1)
                    logger.debug(f"Found Victron manufacturer data for {device.address}")
                    discovered_devices[device.address] = {
                        'device': device,
                        'victron_data': data,
                        'timestamp': datetime.now(timezone.utc)
                    }
                    break

async def scan_and_process_devices():
    """Scan for devices and process them with encryption keys."""
    global discovered_devices
    discovered_devices = {}  # Clear previous discoveries
    
    logger.debug("Scanning for Victron devices...")
    
    # Create an event to signal when we've found a device
    device_found = asyncio.Event()
    
    def detection_callback_with_stop(device, advertisement_data):
        """Modified callback that signals when a device is found."""
        detection_callback(device, advertisement_data)
        # If we found a Victron device with data, signal to stop scanning
        if discovered_devices:
            device_found.set()
    
    scanner = BleakScanner(detection_callback=detection_callback_with_stop)
    
    # Start scanning
    await scanner.start()
    
    try:
        # Wait for either a device to be found or timeout
        await asyncio.wait_for(device_found.wait(), timeout=BLE_SCAN_TIMEOUT)
        logger.debug(f"Device found early, stopping scan")
    except asyncio.TimeoutError:
        # No device found within timeout, that's OK
        logger.debug(f"Scan timeout after {BLE_SCAN_TIMEOUT}s")
    
    await scanner.stop()
    
    logger.debug(f"Scan complete. Found {len(discovered_devices)} Victron device(s)")
    
    # Process discovered devices
    for address, device_info in discovered_devices.items():
        device = device_info['device']
        victron_data = device_info['victron_data']
        
        # Get encryption key if available
        encryption_key = DEVICE_KEYS.get(address)
        
        data_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device_name": device.name,
            "device_address": address
        }
        
        if encryption_key:
            logger.debug(f"Processing {device.name} ({address}) with encryption key")
            try:
                # Detect device type and parse data
                parser_class = detect_device_type(victron_data)
                if parser_class:
                    parser = parser_class(encryption_key)
                    parsed = parser.parse(victron_data)
                    
                    # Convert to dictionary using shared function
                    parsed_dict = parse_victron_data(parsed)
                    
                    logger.debug(f"Parsed Victron data: {parsed_dict}")
                    data_entry["parsed_data"] = parsed_dict
                    data_entry["raw_data"] = victron_data.hex()
                else:
                    logger.warning(f"Could not detect device type for {address}")
                    # Fall back to raw characteristic reading
                    raw_data = await read_raw_characteristics(device)
                    if raw_data:
                        data_entry.update(raw_data)
            except Exception as e:
                logger.warning(f"Could not parse Victron data for {address}: {e}")
                # Fall back to raw characteristic reading
                raw_data = await read_raw_characteristics(device)
                if raw_data:
                    data_entry.update(raw_data)
        else:
            logger.warning(f"No encryption key found for {address}, reading raw characteristics")
            # Read raw characteristics
            raw_data = await read_raw_characteristics(device)
            if raw_data:
                data_entry.update(raw_data)
        
        # Save the data
        save_data(data_entry)

async def read_raw_characteristics(device):
    """Read raw characteristics from the device."""
    try:
        async with BleakClient(device.address) as client:
            logger.info(f"Connected to {device.name}")
            
            # Create a data entry for this reading
            data_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "device_name": device.name,
                "device_address": device.address,
                "readings": {}
            }
            
            # Read data from all services
            for service in client.services:
                for char in service.characteristics:
                    if "read" in char.properties:
                        try:
                            value = await client.read_gatt_char(char.uuid)
                            hex_value = value.hex()
                            logger.info(f"Characteristic {char.uuid}: {hex_value}")
                            data_entry["readings"][char.uuid] = hex_value
                        except Exception as e:
                            logger.error(f"Error reading characteristic {char.uuid}: {str(e)}")
            
            return data_entry

    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return None

def save_data(data_entry):
    """Save data entry to a daily NDJSON file (one JSON object per line)."""
    try:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        json_file = os.path.join(DATA_DIR, f"data_{date_str}.ndjson")
        
        # Flatten the data structure - move parsed_data fields to top level
        if "parsed_data" in data_entry:
            parsed = data_entry.pop("parsed_data")
            # Add each field directly to the data entry
            for key, value in parsed.items():
                data_entry[key] = value
        
        # Append new data as a single line
        with open(json_file, 'a') as f:
            json.dump(data_entry, f, separators=(',', ':'))  # Compact JSON
            f.write('\n')  # Newline delimiter
        
        logger.info(f"Data saved: {data_entry.get('device_name', 'Unknown')} - Battery: {data_entry.get('battery_voltage', 'N/A')}V, Solar: {data_entry.get('solar_power', 'N/A')}W")
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")

async def main():
    logger.info(f"Starting SmartSolar data collection service {VERSION}")
    logger.info(f"Data files will be stored in {DATA_DIR}")
    logger.debug(f"Collection interval: {COLLECTION_INTERVAL}s, BLE scan timeout: {BLE_SCAN_TIMEOUT}s")
    
    while True:
        try:
            # Record start time
            cycle_start = asyncio.get_event_loop().time()
            
            # Reload device keys on each cycle to pick up changes
            global DEVICE_KEYS
            DEVICE_KEYS = load_device_keys()
            
            if DEVICE_KEYS:
                logger.debug(f"Configured with {len(DEVICE_KEYS)} device key(s)")
            else:
                logger.warning("No device encryption keys configured!")
                logger.warning("Add your device key via the web UI or environment variables")
                logger.warning("Falling back to raw characteristic reading...")
            
            # Scan and process devices
            await scan_and_process_devices()
            
            # Calculate how long this cycle took
            cycle_duration = asyncio.get_event_loop().time() - cycle_start
            
            # Calculate remaining time to maintain target interval
            sleep_time = max(0, COLLECTION_INTERVAL - cycle_duration)
            
            if sleep_time > 0:
                logger.debug(f"Cycle took {cycle_duration:.1f}s, sleeping for {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
            else:
                logger.warning(f"Cycle took {cycle_duration:.1f}s, which exceeds target interval of {COLLECTION_INTERVAL}s")
            
        except Exception as e:
            logger.error(f"Main loop error: {str(e)}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main()) 
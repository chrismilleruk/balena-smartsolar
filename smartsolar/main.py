import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from bleak import BleakScanner, BleakClient
import json
from datetime import datetime
import os

# Constants
VERSION = "v1"
SLUG = "smartsolar"
DATA_DIR = f"/data/{SLUG}-{VERSION}"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Configure logging
log_file = os.path.join(DATA_DIR, "smartsolar.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# SmartSolar device UUIDs from discovery
SMARTSOLAR_UUIDS = [
    "306b0001-b081-4037-83dc-e59fcc3cdfd0",
    "68c10001-b17f-4d3a-a290-34ad6499937c",
    "97580001-ddf1-48be-b73e-182664615d8e"
]

async def discover_device():
    """Discover the SmartSolar device."""
    logger.info("Scanning for SmartSolar device...")
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name and "SmartSolar" in device.name:
            logger.info(f"Found SmartSolar device: {device.name} ({device.address})")
            return device
    return None

async def connect_and_read_data(device):
    """Connect to the device and read data from all available characteristics."""
    try:
        async with BleakClient(device.address) as client:
            logger.info(f"Connected to {device.name}")
            
            # Read data from all services
            for service in client.services:
                for char in service.characteristics:
                    if "read" in char.properties:
                        try:
                            value = await client.read_gatt_char(char.uuid)
                            logger.info(f"Characteristic {char.uuid}: {value.hex()}")
                        except Exception as e:
                            logger.error(f"Error reading characteristic {char.uuid}: {str(e)}")

    except Exception as e:
        logger.error(f"Connection error: {str(e)}")

async def main():
    logger.info(f"Starting SmartSolar data collection service v{VERSION}")
    logger.info(f"Log files will be stored in {DATA_DIR}")
    
    while True:
        try:
            device = await discover_device()
            if device:
                await connect_and_read_data(device)
            else:
                logger.warning("SmartSolar device not found")
            
            # Wait before next attempt
            await asyncio.sleep(60)  # Adjust this value based on your needs
            
        except Exception as e:
            logger.error(f"Main loop error: {str(e)}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main()) 
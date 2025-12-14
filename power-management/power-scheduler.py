#!/usr/bin/env python3

"""
Master Power Scheduler for Marine IoT System
Coordinates WiFi, CPU scaling, and service management for optimal power consumption

Based on your analysis:
- Baseline idle: 80mA (4.8Ah/day)  
- Target savings: 25-40mA (1.2-1.9Ah/day = 20-40% reduction)
"""

import asyncio
import logging
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
POWER_MGMT_DIR = Path("/usr/src/app/power-management")
LOG_FILE = "/data/logs/power-scheduler.log"

# Timing configuration (all in seconds)
DATA_COLLECTION_CYCLE = 300    # 5 minutes between BLE collections
WIFI_UPLOAD_INTERVAL = 21600   # 6 hours between uploads  
SLEEP_CYCLE_DURATION = 240     # 4 minutes of deep sleep between collections
UPLOAD_WINDOW_DURATION = 180   # 3 minutes for upload operations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PowerScheduler:
    def __init__(self):
        self.last_upload_time = datetime.now()
        self.in_sleep_mode = False
        
    async def run_script(self, script_name: str, arg: str = None):
        """Run a power management script"""
        script_path = POWER_MGMT_DIR / script_name
        cmd = [str(script_path)]
        if arg:
            cmd.append(arg)
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info(f"Successfully executed: {script_name} {arg or ''}")
            else:
                logger.warning(f"Script {script_name} returned {result.returncode}: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error(f"Script {script_name} timed out")
        except Exception as e:
            logger.error(f"Error running {script_name}: {e}")

    async def enter_sleep_mode(self):
        """Enter deep power saving mode"""
        if self.in_sleep_mode:
            return
            
        logger.info("Entering sleep mode - targeting 50-60mA draw")
        
        # 1. Stop non-essential services (~20mA savings)
        await self.run_script("service-manager.sh", "sleep")
        
        # 2. Disable WiFi (~15mA savings) 
        await self.run_script("wifi-power-mgmt.sh", "disable")
        
        # 3. Scale down CPU (~15mA savings)
        await self.run_script("cpu-scaling.sh", "powersave")
        
        self.in_sleep_mode = True
        logger.info("Sleep mode active - estimated power draw: ~50mA (37% reduction)")

    async def enter_collection_mode(self):
        """Enter mode for data collection"""
        if not self.in_sleep_mode:
            return
            
        logger.info("Entering collection mode")
        
        # Scale up CPU for BLE operations
        await self.run_script("cpu-scaling.sh", "performance")
        
        # Keep WiFi off and services stopped during collection
        self.in_sleep_mode = False
        logger.info("Collection mode active")

    async def enter_upload_mode(self):
        """Enter mode for WiFi uploads"""
        logger.info("Entering upload mode")
        
        # 1. Enable WiFi and wait for connection
        await self.run_script("wifi-power-mgmt.sh", "enable")
        
        # 2. Start upload services
        await self.run_script("service-manager.sh", "upload")
        
        # 3. Ensure CPU is at performance level
        await self.run_script("cpu-scaling.sh", "performance")
        
        self.in_sleep_mode = False
        logger.info("Upload mode active")

    def needs_upload(self) -> bool:
        """Check if it's time for WiFi upload"""
        time_since_upload = datetime.now() - self.last_upload_time
        return time_since_upload.total_seconds() >= WIFI_UPLOAD_INTERVAL

    async def wait_for_data_collection(self):
        """Wait for one data collection cycle to complete"""
        logger.info("Waiting for data collection cycle...")
        await asyncio.sleep(60)  # Give time for BLE collection
        
    async def wait_for_upload_completion(self):
        """Wait for upload operations to complete"""
        logger.info("Waiting for upload completion...")
        await asyncio.sleep(UPLOAD_WINDOW_DURATION)
        self.last_upload_time = datetime.now()

    async def run_power_cycle(self):
        """Run one complete power management cycle"""
        try:
            # Check if upload is needed
            if self.needs_upload():
                logger.info("Upload cycle starting")
                
                # Upload mode
                await self.enter_upload_mode()
                await self.wait_for_upload_completion()
                
                logger.info(f"Next upload in {WIFI_UPLOAD_INTERVAL/3600:.1f} hours")
            
            # Data collection mode  
            await self.enter_collection_mode()
            await self.wait_for_data_collection()
            
            # Sleep mode for remaining cycle time
            await self.enter_sleep_mode()
            sleep_time = SLEEP_CYCLE_DURATION
            
            logger.info(f"Sleeping for {sleep_time/60:.1f} minutes...")
            await asyncio.sleep(sleep_time)
            
        except Exception as e:
            logger.error(f"Error in power cycle: {e}")
            # Fallback to minimal power mode on errors
            await self.enter_sleep_mode()
            await asyncio.sleep(60)

    async def run(self):
        """Main scheduler loop"""
        logger.info("Power scheduler starting")
        logger.info(f"Target power savings: 25-40mA (31-50% reduction from 80mA baseline)")
        
        # Initial upload to establish baseline
        await self.enter_upload_mode()
        await self.wait_for_upload_completion()
        
        while True:
            await self.run_power_cycle()

if __name__ == "__main__":
    scheduler = PowerScheduler()
    try:
        asyncio.run(scheduler.run())
    except KeyboardInterrupt:
        logger.info("Power scheduler stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in power scheduler: {e}")
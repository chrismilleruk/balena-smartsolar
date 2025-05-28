#!/usr/bin/env python3
"""
Shelly Plus Uni monitoring service for balena-zero1-marine
Reads battery voltage and switch states via BLE and logs to NDJSON files
"""

import asyncio
import json
import struct
import random
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import os
import sys
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

# Constants
VERSION = "v1"
SLUG = "shelly"

# Shelly BLE Service and Characteristic UUIDs
SHELLY_SERVICE_UUID = "5f6d4f53-5f52-5043-5f53-56435f49445f"
RPC_CHAR_DATA_UUID = "5f6d4f53-5f52-5043-5f64-6174615f5f5f"
RPC_CHAR_TX_CTL_UUID = "5f6d4f53-5f52-5043-5f74-785f63746c5f"
RPC_CHAR_RX_CTL_UUID = "5f6d4f53-5f52-5043-5f72-785f63746c5f"

# Configuration from environment
SHELLY_MAC = os.getenv('SHELLY_MAC', 'A0:DD:6C:4B:9C:36')
SCAN_INTERVAL = int(os.getenv('SHELLY_SCAN_INTERVAL', '30'))
DATA_DIR = f"/data/{SLUG}-{VERSION}"
LOG_DIR = f"/data/logs/{SLUG}"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
def setup_logging():
    log_file = os.path.join(LOG_DIR, "shelly.log")
    
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
    console_handler.setLevel(logging.INFO)
    
    # Configure root logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()


class ShellyBLEClient:
    """Shelly BLE client for RPC communication"""
    
    def __init__(self, mac_address: str):
        self.mac_address = mac_address
        self._client = None
        self._lock = asyncio.Lock()
        
    async def ensure_connected(self, timeout: float = 10.0) -> BleakClient:
        """Ensure we have a connected client, reconnecting if necessary"""
        async with self._lock:
            if self._client and self._client.is_connected:
                return self._client
                
            # Disconnect existing client if any
            if self._client:
                try:
                    await self._client.disconnect()
                except Exception:
                    pass
                self._client = None
            
            # Try to connect with retries
            for attempt in range(3):
                try:
                    logger.debug(f"Attempting to connect to {self.mac_address} (attempt {attempt + 1}/3)")
                    
                    # First, scan to ensure device is available
                    device = await BleakScanner.find_device_by_address(
                        self.mac_address,
                        timeout=timeout
                    )
                    
                    if not device:
                        logger.warning(f"Device {self.mac_address} not found during scan")
                        if attempt < 2:
                            await asyncio.sleep(2)
                            continue
                        raise Exception(f"Device {self.mac_address} not found after scanning")
                    
                    # Connect to the device
                    self._client = BleakClient(device)
                    await self._client.connect(timeout=timeout)
                    
                    if self._client.is_connected:
                        logger.debug(f"Successfully connected to {self.mac_address}")
                        return self._client
                    else:
                        raise Exception("Connection failed - client not connected")
                        
                except Exception as e:
                    logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        await asyncio.sleep(2)
                    else:
                        raise
                        
    async def disconnect(self):
        """Disconnect the client"""
        async with self._lock:
            if self._client:
                try:
                    await self._client.disconnect()
                except Exception:
                    pass
                self._client = None
                
    async def call_rpc(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """Execute an RPC call to the Shelly device"""
        
        client = await self.ensure_connected()
        
        try:
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
            
        except BleakError as e:
            # Bluetooth-specific errors - mark client as disconnected
            logger.error(f"Bluetooth error during RPC call: {e}")
            await self.disconnect()
            raise
        except Exception as e:
            # Other errors - also disconnect to be safe
            logger.error(f"Error during RPC call: {e}")
            await self.disconnect()
            raise


# Global client instance
shelly_client = None


async def collect_shelly_data():
    """Collect data from Shelly device"""
    global shelly_client
    
    if not shelly_client:
        shelly_client = ShellyBLEClient(SHELLY_MAC)
    
    try:
        # Get device status
        status = await shelly_client.call_rpc("Shelly.GetStatus")
        
        if "result" not in status:
            logger.error("No result in status response")
            return None
            
        result = status["result"]
        
        # Extract relevant data
        data_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device_mac": SHELLY_MAC
        }
        
        # Voltmeter reading (generic - could be any voltage)
        if "voltmeter:100" in result:
            voltmeter = result["voltmeter:100"]
            if "voltage" in voltmeter:
                data_entry["voltmeter_100"] = voltmeter["voltage"]
                logger.debug(f"Voltmeter 100: {voltmeter['voltage']}V")
        
        # Switch states (generic - convert boolean to int for InfluxDB)
        if "switch:0" in result:
            switch0 = result["switch:0"]
            output_state = switch0.get("output", False)
            data_entry["switch_0_output"] = 1 if output_state else 0
            # Also capture power consumption if available
            if "apower" in switch0:
                data_entry["switch_0_power"] = switch0["apower"]
            if "voltage" in switch0:
                data_entry["switch_0_voltage"] = switch0["voltage"]
            if "current" in switch0:
                data_entry["switch_0_current"] = switch0["current"]
            logger.debug(f"Switch 0: {'ON' if output_state else 'OFF'}")
        
        if "switch:1" in result:
            switch1 = result["switch:1"]
            output_state = switch1.get("output", False)
            data_entry["switch_1_output"] = 1 if output_state else 0
            if "apower" in switch1:
                data_entry["switch_1_power"] = switch1["apower"]
            if "voltage" in switch1:
                data_entry["switch_1_voltage"] = switch1["voltage"]
            if "current" in switch1:
                data_entry["switch_1_current"] = switch1["current"]
            logger.debug(f"Switch 1: {'ON' if output_state else 'OFF'}")
        
        # Input states (generic digital inputs)
        if "input:0" in result:
            input0 = result["input:0"]
            state = input0.get("state", False)
            data_entry["input_0_state"] = 1 if state else 0
            if "voltage" in input0:
                data_entry["input_0_voltage"] = input0["voltage"]
            logger.debug(f"Input 0: {'HIGH' if state else 'LOW'}")
        
        if "input:1" in result:
            input1 = result["input:1"]
            state = input1.get("state", False)
            data_entry["input_1_state"] = 1 if state else 0
            if "voltage" in input1:
                data_entry["input_1_voltage"] = input1["voltage"]
            logger.debug(f"Input 1: {'HIGH' if state else 'LOW'}")
        
        # Device temperature
        if "temperature:0" in result:
            temp = result["temperature:0"]
            if "tC" in temp:
                data_entry["device_temp_c"] = temp["tC"]
                logger.debug(f"Device temperature: {temp['tC']}°C")
            if "tF" in temp:
                data_entry["device_temp_f"] = temp["tF"]
        
        # System info
        if "sys" in result:
            sys_info = result["sys"]
            if "uptime" in sys_info:
                data_entry["uptime"] = sys_info["uptime"]
            if "ram_size" in sys_info:
                data_entry["ram_size"] = sys_info["ram_size"]
            if "ram_free" in sys_info:
                data_entry["ram_free"] = sys_info["ram_free"]
            if "fs_size" in sys_info:
                data_entry["fs_size"] = sys_info["fs_size"]
            if "fs_free" in sys_info:
                data_entry["fs_free"] = sys_info["fs_free"]
        
        # WiFi status
        if "wifi" in result:
            wifi = result["wifi"]
            data_entry["wifi_connected"] = 1 if wifi.get("sta_ip") is not None else 0
            if "rssi" in wifi:
                data_entry["wifi_rssi"] = wifi["rssi"]
            if "ssid" in wifi:
                data_entry["wifi_ssid"] = wifi["ssid"]
            logger.debug(f"WiFi: {wifi.get('ssid', 'N/A')}, RSSI: {wifi.get('rssi', 'N/A')} dBm")
        
        # BLE status
        if "ble" in result:
            ble = result["ble"]
            data_entry["ble_enabled"] = 1 if ble.get("enable", False) else 0
        
        # Log a summary of the collected data
        voltage = data_entry.get("voltmeter_100", "N/A")
        switch0 = "ON" if data_entry.get("switch_0_output", 0) else "OFF"
        switch1 = "ON" if data_entry.get("switch_1_output", 0) else "OFF"
        temp = data_entry.get("device_temp_c", "N/A")
        
        logger.info(f"Data collected: Voltage: {voltage}V, Switch0: {switch0}, Switch1: {switch1}, Temp: {temp}°C")
        
        return data_entry
        
    except Exception as e:
        logger.error(f"Error collecting data: {e}")
        return None


def save_data(data_entry):
    """Save data entry to a daily NDJSON file"""
    try:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ndjson_file = os.path.join(DATA_DIR, f"data_{date_str}.ndjson")
        
        # Append new data as a single line
        with open(ndjson_file, 'a') as f:
            json.dump(data_entry, f, separators=(',', ':'))  # Compact JSON
            f.write('\n')  # Newline delimiter
        
        logger.debug(f"Data appended to {ndjson_file}")
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")


async def main():
    logger.info(f"Starting Shelly monitoring service {VERSION}")
    logger.info(f"Monitoring device: {SHELLY_MAC}")
    logger.debug(f"Scan interval: {SCAN_INTERVAL}s")
    logger.debug(f"Data files: {DATA_DIR}")
    logger.debug(f"Log files: {LOG_DIR}")
    
    # Initial delay to let system settle
    await asyncio.sleep(5)
    
    consecutive_failures = 0
    max_consecutive_failures = 10
    backoff_delay = 5  # Initial backoff delay in seconds
    max_backoff_delay = 300  # Maximum backoff delay (5 minutes)
    
    while True:
        try:
            # Record start time
            cycle_start = asyncio.get_event_loop().time()
            
            # Collect data from Shelly
            data = await collect_shelly_data()
            
            if data:
                save_data(data)
                consecutive_failures = 0  # Reset failure counter on success
                backoff_delay = 5  # Reset backoff delay
            else:
                consecutive_failures += 1
                logger.warning(f"Failed to collect data (attempt {consecutive_failures}/{max_consecutive_failures})")
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"Too many consecutive failures ({consecutive_failures}), will continue retrying with backoff")
                    # Don't exit, just use maximum backoff
                    await asyncio.sleep(max_backoff_delay)
                    consecutive_failures = 0  # Reset counter but keep trying
                    continue
                else:
                    # Exponential backoff for retries
                    current_backoff = min(backoff_delay * (2 ** (consecutive_failures - 1)), max_backoff_delay)
                    logger.info(f"Waiting {current_backoff}s before retry...")
                    await asyncio.sleep(current_backoff)
                    continue
            
            # Calculate how long this cycle took
            cycle_duration = asyncio.get_event_loop().time() - cycle_start
            
            # Calculate remaining time to maintain target interval
            sleep_time = max(0, SCAN_INTERVAL - cycle_duration)
            
            if sleep_time > 0:
                logger.debug(f"Cycle took {cycle_duration:.1f}s, sleeping for {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
            else:
                logger.warning(f"Cycle took {cycle_duration:.1f}s, which exceeds target interval of {SCAN_INTERVAL}s")
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down gracefully...")
            if shelly_client:
                await shelly_client.disconnect()
            break
        except Exception as e:
            logger.error(f"Main loop error: {str(e)}", exc_info=True)
            consecutive_failures += 1
            
            # Exponential backoff for unexpected errors
            current_backoff = min(backoff_delay * (2 ** (consecutive_failures - 1)), max_backoff_delay)
            logger.info(f"Waiting {current_backoff}s before retry...")
            await asyncio.sleep(current_backoff)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1) 
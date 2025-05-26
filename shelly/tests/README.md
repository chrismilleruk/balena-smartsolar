# Shelly BLE Test Scripts

This directory contains test scripts used during the development of the Shelly BLE integration.

## Main Files

- **`shelly_ble_client.py`** - The working BLE client implementation that was ported to the main shelly container
- **`test_shelly.py`** - Simple test script to verify Shelly connection and data collection before deployment

## Development/Debug Scripts

These scripts were used during protocol discovery and debugging:

- **`test_shelly_discover.py`** - BLE device discovery script
- **`test_shelly_bluetooth.py`** - Low-level Bluetooth testing
- **`test_shelly_protocol.py`** - Protocol exploration and testing
- **`test_shelly_debug.py`** - Debug version with verbose logging
- **`test_shelly_rpc_working.py`** - RPC protocol testing
- **`test_shelly_simple.py`** - Simplified connection test

## Usage

To test the Shelly connection locally before deploying:

```bash
cd shelly/tests
python3 test_shelly.py
```

This will verify:
1. BLE connection to the Shelly device
2. Device info retrieval
3. Status reading (voltages, switches, temperature)
4. Data collection function

## Notes

- The Shelly Plus Uni uses a JSON-RPC protocol over BLE
- Service UUID: `5f6d4f53-5f52-5043-5f53-56435f49445f`
- Default MAC address: `A0:DD:6C:4B:9C:36` (can be overridden with SHELLY_MAC env var) 
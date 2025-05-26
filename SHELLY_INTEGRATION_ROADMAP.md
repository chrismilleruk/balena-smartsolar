# Shelly Plus Uni Integration Roadmap

## Overview

This document outlines the integration of a Shelly Plus Uni device into the balena-zero1-marine monitoring system. The Shelly Plus Uni will:
- Read battery voltage for the 2nd battery via analog input
- Control WiFi circuit power via relay output
- Communicate over Bluetooth Low Energy (BLE)

## Current Status ✅

### Hardware Configuration
- **Device**: Shelly Plus Uni (MAC: A0:DD:6C:4B:9C:36)
- **Analog Input**: Connected to Battery 2 voltage divider
- **Switch 0**: Controls WiFi power circuit
- **Network**: Connected to "H4IoT" WiFi (192.168.11.253)

### Working Proof of Concept
- Successfully communicating with Shelly over BLE using official RPC protocol
- Reading battery voltage: `voltmeter:100` = 12.5V
- Reading switch states: `switch:0` (WiFi power) currently OFF
- Network status confirmed: WiFi connected with strong signal (-39 dBm)

### Test Files (moved to `shelly/tests/`)
- `shelly_ble_client.py` - Simplified working client
- Various test scripts for protocol discovery

## Architecture Decision

### Simplified Monitoring Architecture

The Shelly device handles all scheduling and control logic natively through its scripting engine. The Python container serves purely as a monitoring and logging service - no control logic, just simple state observation and recording.

### Container Strategy

Separate containers for clean separation of concerns:
- **shelly** container: Monitors Shelly device via BLE, writes NDJSON
- **smartsolar** container: Existing container for Victron monitoring
- **telegraf** container: Reads all NDJSON files, sends to InfluxDB Cloud
- **dashboard** container: Extended to display data from both sources

### Data Flow

```
Shelly Device (handles all scheduling/control logic)
     ↓ BLE
shelly container (simple monitoring only)
     ↓ NDJSON
/data/shelly-v1/data_YYYY-MM-DD.ndjson
     ↓
Telegraf → InfluxDB Cloud

SmartSolar → smartsolar container → /data/smartsolar-v1/data_*.ndjson
                                          ↓
                                      Telegraf
```

## Implementation Plan (Simplified)

### Phase 1: Minimum Viable Product (Required for Boat Installation)

#### 1.1 Create Shelly Container ✅
- [x] Create new `shelly` container structure
  - [x] Copy patterns from existing `smartsolar` container
  - [x] Dockerfile based on Alpine/Python (same as smartsolar)
  - [x] docker-compose.yml service definition
- [x] Port working BLE client code (`shelly_ble_client.py`)
- [x] Implement monitoring loop (30-second intervals)
  - [x] Read battery voltage (generic `voltmeter_100` field)
  - [x] Read switch states (generic `switch_0_output`, `switch_1_output`)
  - [x] Read device temperature
  - [x] Read input states
  - [x] Read system info (uptime, memory, storage)
  - [x] Read WiFi status
- [x] Add NDJSON logging using same pattern as smartsolar
  - [x] Use TimedRotatingFileHandler (daily rotation, 30 days retention)
  - [x] Write to `/data/shelly-v1/data_YYYY-MM-DD.ndjson`
  - [x] Convert booleans to integers for InfluxDB compatibility
- [x] Use generic field names (not application-specific)
- [x] Organize test files in `shelly/tests/`
- [x] Version-based data paths for future compatibility

#### 1.2 Configure Shelly Device
- [ ] Upload WiFi scheduling script to Shelly
  - [ ] 5-minute windows every hour (12:00-22:00)
  - [ ] Test schedule works correctly
- [ ] Calibrate analog input for accurate battery voltage
- [ ] Test manual override functionality

#### 1.3 Update Existing Infrastructure
- [x] Configure Telegraf to monitor `/data/shelly-*/data_*.ndjson`
- [ ] Extend existing dashboard to show:
  - [ ] Battery 2 voltage gauge (using `voltmeter_100`)
  - [ ] WiFi power state indicator (using `switch_0_output`)
  - [ ] Shelly device temperature

#### 1.4 Testing Before Installation
- [ ] 48-hour continuous operation test
- [ ] Verify BLE connection stability
- [ ] Confirm data flowing to InfluxDB Cloud
- [ ] Test container auto-restart on failure

### Phase 2: Future Enhancements (After Proven Stable)
- SignalK integration (if needed for local displays)
- Advanced error handling and connection management
- Historical analysis features
- Event-based logging for switch state changes

## Technical Details

### BLE RPC Protocol
The Shelly Plus Uni uses a JSON-RPC protocol over BLE with:
- Service UUID: `5f6d4f53-5f52-5043-5f53-56435f49445f`
- TX Control: `5f6d4f53-5f52-5043-5f74-785f63746c5f` (write length)
- Data: `5f6d4f53-5f52-5043-5f64-6174615f5f5f` (write request/read response)
- RX Control: `5f6d4f53-5f52-5043-5f72-785f63746c5f` (read length)

### Key RPC Methods
- `Shelly.GetStatus` - Read all inputs/outputs/voltages
- `Switch.Set` - Control relay outputs (only for initial setup/testing)

### NDJSON File Format
Following the same pattern as smartsolar, with generic field names:
```json
{"timestamp": "2024-01-15T10:30:00Z", "voltmeter_100": 12.5, "switch_0_output": 1, "switch_1_output": 0, "device_temp_c": 23.4}
{"timestamp": "2024-01-15T10:30:30Z", "voltmeter_100": 12.4, "switch_0_output": 1, "switch_1_output": 0, "device_temp_c": 23.5}
```

### File Paths
- **Data**: `/data/shelly-v1/data_YYYY-MM-DD.ndjson`
- **Logs**: `/data/logs/shelly/shelly.log`
- **Version**: When NDJSON format changes, increment version (e.g., `shelly-v2`)

## Environment Variables
```bash
# Shelly device configuration
SHELLY_MAC=A0:DD:6C:4B:9C:36
SHELLY_SCAN_INTERVAL=30

# All scheduling is handled by Shelly device scripts
# Python container only monitors and logs
```

## Success Criteria for Installation
- ✅ BLE connection stable over 48 hours
- ✅ Battery voltage readings accurate (±0.1V)
- ✅ Data flowing to InfluxDB Cloud
- ✅ Shelly scheduling script working correctly
- ✅ Container auto-restarts on failure
- ✅ Dashboard showing Battery 2 voltage and WiFi state

## References
- Working BLE client: `shelly/tests/shelly_ble_client.py`
- SmartSolar patterns to copy: `smartsolar/main.py` 
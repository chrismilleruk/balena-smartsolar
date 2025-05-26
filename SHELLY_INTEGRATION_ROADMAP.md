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

### Test Files (moved to `smartsolar/shelly-tests/`)
- `shelly_ble_client.py` - Simplified working client
- Various test scripts for protocol discovery

## Architecture Decision

### Separate Container Approach ✅
Create a dedicated `shelly` container separate from `smartsolar` because:
- Different concerns (battery monitoring vs power management)
- Clean separation of responsibilities
- Easier maintenance and updates
- Independent scaling/restart capabilities

### Library Strategy
- **Option A**: Use official Shelly BLE RPC script from GitHub
  - Pros: Official support, full features, maintained by Shelly
  - Cons: Not packaged, need to vendor or git submodule
- **Option B**: Create minimal custom implementation
  - Pros: Lightweight, only what we need
  - Cons: Maintenance burden, missing features

**Recommendation**: Start with our working minimal implementation, consider official script if we need advanced features.

## Implementation Checklist

### Phase 1: Basic Integration
- [ ] Create new `shelly` container structure
  - [ ] Dockerfile based on Alpine/Python
  - [ ] docker-compose.yml service definition
  - [ ] Basic project structure
- [ ] Move working BLE client code to new container
- [ ] Implement periodic monitoring loop
  - [ ] Read battery voltage every 30 seconds
  - [ ] Read switch states
  - [ ] Monitor network status
- [ ] Add MQTT publishing
  - [ ] Publish battery voltage to `boat/battery2/voltage`
  - [ ] Publish switch states to `boat/wifi/power`
  - [ ] Publish device status/health

### Phase 2: Power Management Logic
- [ ] Implement battery-based WiFi control
  - [ ] Turn off WiFi when battery < threshold (e.g., 11.5V)
  - [ ] Hysteresis to prevent rapid switching
  - [ ] Manual override capability
- [ ] Add time-based controls
  - [ ] Schedule WiFi on/off times
  - [ ] Respect battery priority over schedule
- [ ] Implement graceful shutdown warnings
  - [ ] MQTT notification before WiFi shutdown
  - [ ] Countdown timer

### Phase 3: Advanced Features
- [ ] Web API endpoints
  - [ ] GET /status - Current state
  - [ ] POST /wifi/power - Manual control
  - [ ] GET /config - Current thresholds
  - [ ] POST /config - Update thresholds
- [ ] Historical data logging
  - [ ] Store voltage readings
  - [ ] Track power state changes
  - [ ] Calculate WiFi uptime statistics
- [ ] Integration with existing dashboard
  - [ ] Add Battery 2 voltage display
  - [ ] WiFi power control widget
  - [ ] Status indicators

### Phase 4: Reliability & Monitoring
- [ ] Connection management
  - [ ] Auto-reconnect on BLE failure
  - [ ] Exponential backoff
  - [ ] Connection status reporting
- [ ] Error handling
  - [ ] Graceful degradation
  - [ ] Alert on communication failure
  - [ ] Fallback to safe state
- [ ] Health checks
  - [ ] Liveness probe for container
  - [ ] BLE connection health
  - [ ] MQTT connection health

## Technical Details

### BLE RPC Protocol
The Shelly Plus Uni uses a JSON-RPC protocol over BLE with:
- Service UUID: `5f6d4f53-5f52-5043-5f53-56435f49445f`
- TX Control: `5f6d4f53-5f52-5043-5f74-785f63746c5f` (write length)
- Data: `5f6d4f53-5f52-5043-5f64-6174615f5f5f` (write request/read response)
- RX Control: `5f6d4f53-5f52-5043-5f72-785f63746c5f` (read length)

Protocol flow:
1. Write request length (4 bytes, big-endian) to TX Control
2. Write JSON-RPC request to Data characteristic
3. Read response length from RX Control
4. Read response data from Data characteristic

### Key RPC Methods
- `Shelly.GetStatus` - Read all inputs/outputs/voltages
- `Shelly.GetConfig` - Read configuration
- `Switch.Set` - Control relay outputs
- `Switch.Toggle` - Toggle relay state

### MQTT Topics Structure
```
boat/shelly/status          # Online/offline status
boat/shelly/battery2/voltage # Battery 2 voltage reading
boat/shelly/wifi/power      # WiFi power state (on/off)
boat/shelly/wifi/control    # Command topic for manual control
boat/shelly/config/...      # Configuration parameters
```

## Environment Variables
```bash
# Shelly device configuration
SHELLY_MAC=A0:DD:6C:4B:9C:36
SHELLY_SCAN_INTERVAL=30

# Battery thresholds
BATTERY_LOW_VOLTAGE=11.5
BATTERY_RECOVERY_VOLTAGE=12.0

# MQTT configuration
MQTT_BROKER=mqtt
MQTT_PORT=1883
MQTT_CLIENT_ID=shelly-monitor

# WiFi control
WIFI_AUTO_CONTROL=true
WIFI_SCHEDULE_ENABLED=false
```

## Questions for Next Steps

1. **Battery Voltage Calibration**: Do we need to calibrate the analog input reading?
2. **Power Control Logic**: What should be the exact thresholds and hysteresis values?
3. **Manual Override**: How long should manual overrides last before reverting to auto?
4. **Integration Priority**: Which dashboard integration features are most important?
5. **Backup Power**: Should we implement different behavior when on shore power?

## References
- [Official Shelly BLE RPC Documentation](https://kb.shelly.cloud/knowledge-base/kbsa-mastering-shelly-iot-devices-a-comprehensive-)
- [Shelly Plus Uni Manual](https://www.shelly.com/products/shelly-plus-uni)
- Official GitHub: https://github.com/ALLTERCO/Utilities/tree/main/shelly-ble-rpc 
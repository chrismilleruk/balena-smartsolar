# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a BalenaOS-based marine monitoring system that collects data from Victron SmartSolar charge controllers and Shelly Plus Uni devices via Bluetooth Low Energy (BLE). The system runs on Raspberry Pi devices and provides real-time monitoring with cloud sync capabilities.

## Architecture

The system consists of 5 containerized services defined in `docker-compose.yml`:

### Core Services
- **smartsolar**: BLE data collection from Victron SmartSolar MPPT charge controllers with encrypted data parsing
- **shelly**: BLE monitoring of Shelly Plus Uni devices for battery voltage and switch control
- **telegraf**: Data pipeline that syncs NDJSON files to InfluxDB Cloud with offline buffering
- **web**: Flask-based service dashboard with QR codes for easy mobile access
- **cloudflared**: Optional secure tunnel for remote access via Cloudflare

### Data Flow
1. BLE services scan and collect data every 30-60 seconds
2. Data stored as daily NDJSON files in `/data/<service>-v1/`
3. Telegraf tails NDJSON files and streams to InfluxDB Cloud
4. Web dashboard provides local access and service status

## Essential Development Commands

### Balena Deployment
```bash
# Deploy to Balena device (replace with your device/app name)
balena push <app-name>

# SSH into services for debugging
balena device ssh <device-uuid> smartsolar
balena device ssh <device-uuid> shelly
```

### Service-Specific Development

#### SmartSolar Service
```bash
# Debug BLE connectivity and parsing
./debug_system.sh
python3 debug_bluetooth.py
python3 debug_victron_reader.py

# Test specific device (set in environment)
SMARTSOLAR_TARGET_DEVICE=XX:XX:XX:XX:XX:XX python3 debug_victron_reader.py
```

#### Shelly Service
```bash
# Run tests for Shelly BLE communication
cd shelly/tests
python3 test_shelly_bluetooth.py
python3 test_shelly_rpc_working.py

# Test with specific MAC address
SHELLY_MAC=XX:XX:XX:XX:XX:XX python3 main.py
```

#### Telegraf Service
```bash
# Test configuration
telegraf --config /etc/telegraf/telegraf.conf --test

# View available plugins
telegraf --input-list
```

### Local Development & Testing
```bash
# Check logs for all services
docker-compose logs -f

# Restart specific service
docker-compose restart smartsolar

# View data files
ls -la /data/
tail -f /data/smartsolar-v1/data_$(date +%Y-%m-%d).ndjson
```

## Key Configuration Areas

### Device Encryption Keys (Victron)
Three methods to configure SmartSolar encryption keys:
1. **Web UI**: Access device dashboard → "Manage Keys"
2. **Environment**: `SMARTSOLAR_KEY_XX_XX_XX_XX_XX_XX=32_char_hex_key`
3. **JSON file**: `/data/smartsolar-keys.json`

### Environment Variables
Critical settings in `docker-compose.yml`:
- `BLE_SCAN_TIMEOUT`: BLE scanning duration (1-30s, default: 5s)
- `COLLECTION_INTERVAL`: Data collection frequency (≥10s, default: 60s)
- `SHELLY_MAC`: Target Shelly device MAC address
- `INFLUX_TOKEN/ORG/BUCKET`: InfluxDB Cloud credentials

## Code Architecture Patterns

### BLE Communication Pattern
Both services follow similar patterns:
1. **Async BLE scanning** with device-specific callbacks
2. **Connection management** with retry logic and exponential backoff
3. **Error handling** with graceful degradation to raw data collection
4. **NDJSON logging** with daily file rotation and 30-day retention

### Key Shared Components
- `key_manager.py`: Unified encryption key management for Victron devices
- Device-specific parsers: Victron uses `victron-ble` library, Shelly uses custom JSON-RPC over BLE
- Logging: TimedRotatingFileHandler with console + file output

### Data Storage Convention
- Path: `/data/<service>-<version>/`
- Format: `data_YYYY-MM-DD.ndjson` (one JSON object per line)
- Retention: 30 days automatic cleanup
- Schema: Each line contains `timestamp`, `device_*` fields, and parsed metrics

## Deployment & Release Process

### Version Management
Update these 3 files for releases:
1. `VERSION` - Main version file
2. `CHANGELOG.md` - Release notes with date
3. `balena.yml` - Update version field

### Release Commands
```bash
# Tag and release
git commit -m "Release vX.Y.Z - description"
git tag vX.Y.Z
git push origin <branch> --tags

# Deploy to fleet
balena push <fleet-name>
```

### Environment Setup
- Target device: `raspberrypi0-wifi` (primary), supports Pi 0-4
- Network: `host` mode required for BLE access
- Privileges: Containers need `privileged: true` for Bluetooth access
- Features: `dbus`, `kernel-modules`, `balena-api` labels required

## Debugging & Monitoring

### System Health Checks
- **BLE Status**: `hciconfig hci0` in smartsolar/shelly containers
- **Data Pipeline**: Check NDJSON file timestamps and Telegraf logs
- **Cloud Sync**: Monitor Telegraf connection to InfluxDB Cloud

### Common Issues
- **"No Victron devices found"**: Check BLE range, "Instant Readout" enabled in VictronConnect app
- **"No encryption key found"**: Configure keys via web UI or environment variables
- **"Could not parse data"**: Verify encryption key correctness, check firmware compatibility
- **Telegraf sync failures**: Check InfluxDB credentials and network connectivity

### Log Locations
- Application logs: Container stdout (visible in Balena dashboard)
- Error logs: `/data/<service>-v1/<service>.log*` (30-day rotation)
- Data files: `/data/<service>-v1/data_*.ndjson`

## Testing Infrastructure

The shelly service includes comprehensive test suites in `shelly/tests/` covering:
- BLE device discovery and connection
- JSON-RPC protocol implementation
- Timer detection and control logic
- Autooff functionality

Use these tests as references when extending BLE functionality to other services.

## Troubleshooting Data Gaps & Intermittent Connectivity

### Engagement Model for Intermittent Devices

When diagnosing issues with marine IoT devices that have limited connectivity windows:

1. **Analysis-First Approach**: Avoid generating diagnostic code immediately
2. **Leverage Available Data**: Use existing cloud data (InfluxDB/Grafana) for investigation
3. **Manual Query Execution**: Operator runs SQL queries in InfluxDB/Grafana rather than device console
4. **Targeted Investigation**: Focus analysis on specific time windows when device reconnects
5. **Defer Device Access**: Only SSH into device once hypothesis is formed

### Power Loss Detection Using Cloud Data

The monitoring system is powered by the same battery it monitors. During severe undervoltage events, the Pi may shut down completely.

**Check for power cycles using system_stats measurement:**
```sql
SELECT 
  DATE_TRUNC('day', time) AS day,
  MIN(uptime) AS min_uptime,
  MAX(uptime) AS max_uptime,
  COUNT(*) AS readings
FROM "system_stats"
WHERE time >= 'YYYY-MM-DD' AND time <= 'YYYY-MM-DD'
GROUP BY DATE_TRUNC('day', time)
ORDER BY day
```

**Power loss indicators:**
- `min_uptime` near 0-500 seconds = fresh reboot after power loss
- Missing days in query results = complete power outage periods
- Low `readings` count = partial day operation before shutdown
- Normal operation shows 1440 readings/day with steady uptime progression

**Cross-reference with battery voltage data:**
- Export voltage trends as CSV from Grafana
- Look for correlation between voltage drops (<8.5V) and missing system_stats
- Voltage crashes often precede data gaps by hours

### Data Recovery Expectations

- **Complete power loss**: No local data exists during outage, cannot be recovered
- **Service crash only**: Local NDJSON files may exist, Telegraf will auto-sync on reconnect
- **Sync issues**: Force re-sync by clearing Telegraf state (rare)

### Voltage Monitoring Critical Thresholds
- **System shutdown**: ~8.4V and below (Pi cannot operate)
- **Instability range**: 8.4V - 10V (random shutdowns likely)
- **Stable operation**: 11V+ recommended for reliable monitoring

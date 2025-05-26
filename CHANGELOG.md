# Changelog

## [0.2.0] - 2025-05-26

### New Features

#### Shelly Plus Uni Integration
- **New Container**: Added dedicated `shelly` container for monitoring Shelly Plus Uni devices via BLE
- **BLE RPC Protocol**: Implemented Shelly's JSON-RPC over BLE for reliable communication
- **Generic Data Collection**: Monitors all available Shelly data points:
  - Voltmeter readings (analog inputs)
  - Switch states and power consumption
  - Digital input states
  - Device temperature
  - System information (uptime, memory, storage)
  - WiFi status and signal strength
- **InfluxDB Compatibility**: Converts boolean values to integers (0/1) for proper storage

#### Architecture Improvements
- **Multi-Device Support**: Extended architecture to support multiple device types
- **Shared Infrastructure**: Telegraf now monitors both SmartSolar and Shelly data
- **Generic Field Names**: Shelly container uses generic field names for reusability:
  - `voltmeter_100` instead of battery-specific names
  - `switch_0_output`, `switch_1_output` instead of application-specific names
  - Allows the same container to be used for different Shelly deployments

#### Data Management
- **NDJSON Format**: Consistent with SmartSolar, using daily rotating files
- **30-Day Retention**: Automatic log rotation and cleanup
- **Separate Data Paths**: `/data/shelly/` for Shelly, `/data/smartsolar-v1/` for SmartSolar

### Improvements
- **Test Organization**: Moved Shelly test scripts to `shelly/tests/` directory
- **Documentation**: Added comprehensive roadmap for Shelly integration
- **Error Handling**: Auto-restart after 10 consecutive failures for resilience

### Technical Details
- **Shelly BLE Service UUID**: `5f6d4f53-5f52-5043-5f53-56435f49445f`
- **Configurable Scan Interval**: Default 30 seconds via `SHELLY_SCAN_INTERVAL`
- **Python 3 Alpine**: Consistent base image across containers

## [0.1.1] - 2025-05-26

### Improvements

#### Data Collection Timing
- **Adaptive BLE Scanning**: Scan stops immediately when device is found (previously fixed 10s)
- **Configurable Intervals**: New environment variables for timing control:
  - `BLE_SCAN_TIMEOUT`: Maximum scan duration (1-30s, default: 5s)
  - `COLLECTION_INTERVAL`: Time between collections (min: 10s, default: 60s)
- **Consistent Timing**: Dynamic sleep adjustment maintains regular intervals
- **Reduced Latency**: Typical scan time reduced from 10s to 1-2s

#### Reliability Enhancements
- **Internet Outage Handling**: Improved documentation and testing of offline scenarios
- **Power Loss Recovery**: Verified data persistence across power cycles
- **State Persistence**: Telegraf maintains file positions through restarts
- **Buffer Management**: Clear understanding of 10,000 metric memory buffer (~83 hours)

#### Configuration
- **Environment Variables**: All timing parameters now configurable without code changes
- **Validation**: Safe bounds checking for all configurable parameters
- **Logging**: Added timing debug information for monitoring collection cycles

### Documentation
- Added detailed explanation of outage recovery behavior
- Documented Telegraf retry configuration options
- Updated README with new environment variables

## [0.1.0] - 2024-12-20

### Initial Release

#### Core Features
- **BLE Data Collection**: Automatic discovery and data collection from Victron SmartSolar devices
- **Encryption Support**: Decrypts Victron BLE advertisement data using device-specific keys
- **Web Dashboard**: Real-time monitoring interface with key management
- **Data Persistence**: NDJSON format daily log files with efficient append-only writes

#### Cloud Sync
- **InfluxDB Cloud Integration**: Telegraf-based sync with intermittent connectivity support
  - Persistent disk buffering (up to 500MB)
  - Automatic catch-up after disconnections (up to 7 days)
  - Real-time streaming with <5 minute lag when connected
  - State tracking across container restarts

#### Key Management
- Three configuration methods:
  - Web UI interface
  - Environment variables
  - JSON configuration file
- Dynamic key reloading without restart

#### Data Formats
- Supports both encrypted data (with parsed metrics) and raw characteristic readings
- NDJSON format for efficient streaming and processing
- Comprehensive metric collection including:
  - Battery voltage and current
  - Solar power and daily yield
  - Charge state and errors
  - Device temperature

#### Developer Tools
- Debug scripts for Bluetooth connectivity testing
- Migration script for JSON to NDJSON conversion
- Comprehensive logging with daily rotation

#### Infrastructure
- Docker-based deployment on BalenaOS
- Persistent volumes for data and state
- Health checks and automatic restarts
- Support for Raspberry Pi Zero W and other Balena-supported devices
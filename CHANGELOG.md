# Changelog

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
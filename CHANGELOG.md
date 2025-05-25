# Changelog

## [1.0.0] - 2024-12-19

### Added
- Created `key_manager.py` module with shared key management functions
- Added comprehensive `README.md` with setup instructions and troubleshooting guide
- Created `CHANGELOG.md` to track project changes

### Changed
- Renamed `victron_reader.py` to `debug_victron_reader.py` to clarify its purpose as a debug tool
- Updated `main.py`, `dashboard.py`, and `debug_victron_reader.py` to use shared `key_manager` module
- Improved code organization by extracting common functions
- Modified `main.py` to use detection callback for proper BLE advertisement data capture
- Updated to use timezone-aware datetime objects (replacing deprecated `utcnow()`)
- Keys are now reloaded on each scan cycle (every 60 seconds) for dynamic updates

### Fixed
- Fixed indentation issues in `main.py`
- Removed duplicate key management code across multiple files
- Fixed view switching issue in dashboard where keys section wasn't hidden when loading data
- Fixed BLE advertisement data not being captured in main.py by switching to callback-based scanning
- Added user feedback about key loading timing in the web UI

### Documentation
- Added detailed instructions for obtaining and configuring encryption keys
- Documented three methods for key configuration (Web UI, Environment Variables, JSON file)
- Added troubleshooting section for common issues
- Included architecture overview and data export information 
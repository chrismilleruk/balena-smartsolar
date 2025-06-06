# SmartSolar BLE Data Collection for BalenaOS

This project enables Bluetooth Low Energy (BLE) data collection from Victron SmartSolar charge controllers on Raspberry Pi devices running BalenaOS. It decrypts and stores solar charging data, providing a web dashboard for monitoring.

## Features

- 🔋 Real-time battery monitoring (voltage, current, state of charge)
- ☀️ Solar panel performance tracking (power, daily yield)
- 📊 Historical data logging with daily JSON files
- 🌐 Web dashboard for live monitoring
- 🔐 Secure device pairing with encryption keys
- 📱 Bluetooth Low Energy (BLE) communication
- 🐳 Runs on Balena OS for easy deployment and management
- ☁️ Automatic sync to InfluxDB Cloud with offline buffering

## Supported Devices

- Victron SmartSolar MPPT charge controllers with Bluetooth
- Tested on Raspberry Pi Zero W
- Should work with any BalenaOS-supported device with Bluetooth

## Quick Start

### 1. Deploy to BalenaOS

Push this repository to your Balena application:

```bash
git clone <this-repo>
cd balena-zero1-marine
balena push <your-app-name>
```

### 2. Get Your Encryption Key

Each Victron device uses encryption for BLE data. To get your device's key:

1. Install the **VictronConnect** app on your phone/computer
2. Connect to your SmartSolar device
3. Navigate to: **Settings → Product Info**
4. Enable **"Instant Readout via Bluetooth"**
5. Click **"Show"** next to "Instant Readout Details"
6. Copy the **encryption key** (32 character hex string)

### 3. Configure Encryption Keys

You have three options to configure encryption keys:

#### Option A: Web UI (Recommended)
1. Access your device's web dashboard at `http://<device-ip>`
2. Click **"Manage Keys"**
3. Enter your device's MAC address (e.g., `DF:C9:B0:6E:3F:EF`)
4. Enter the encryption key
5. Click **"Save Key"**

#### Option B: Environment Variables
Add to your `docker-compose.yml`:

```yaml
smartsolar:
  environment:
    - SMARTSOLAR_KEY_DF_C9_B0_6E_3F_EF=your_32_char_encryption_key_here
```

Note: Replace colons (`:`) with underscores (`_`) in the MAC address.

#### Option C: JSON File
SSH into your device and create `/data/smartsolar-keys.json`:

```json
{
  "devices": {
    "DF:C9:B0:6E:3F:EF": "your_32_char_encryption_key_here"
  }
}
```

## Data Access

### Web Dashboard
- URL: `http://<device-ip>/smartsolar`
- Features:
  - Real-time data display
  - Historical data viewing
  - Key management interface
- Note: The SmartSolar dashboard is now integrated into the main web interface

### Data Files
- Location: `/data/smartsolar-v1/`
- Format: Daily JSON files (`data_YYYY-MM-DD.ndjson`)
- Contains: Timestamp, device info, and all solar metrics

### Available Metrics
- Battery voltage (V)
- Battery charging current (A)
- Solar panel voltage (V)
- Solar power (W)
- Daily yield (Wh)
- Charge state (OFF, BULK, ABSORPTION, FLOAT)
- External load current (A)
- Device temperature (°C)

### Cloud Sync (Optional)

The included Telegraf service can sync your data to InfluxDB Cloud:
- Handles intermittent connectivity with persistent buffering
- Automatically catches up after disconnections (up to 7 days)
- Real-time streaming when connected (<5 minute lag)
- See [telegraf/README.md](telegraf/README.md) for setup instructions

## Debugging

### Check Bluetooth Connectivity
```bash
balena ssh <device> smartsolar
./debug_system.sh
./debug_bluetooth.py
```

### Test Encryption Keys
```bash
balena ssh <device> smartsolar
python3 debug_victron_reader.py
```

This will show if keys are working and display parsed data.

### View Logs
- Info logs: Balena dashboard console
- Error logs: `/data/smartsolar-v1/smartsolar.log*`

## Architecture

```
smartsolar/
├── main.py                 # Main data collection service
├── dashboard.py            # Web dashboard server
├── key_manager.py          # Shared key management functions
├── debug_victron_reader.py # Debug tool for testing
├── templates/
│   └── index.html         # Dashboard UI
└── start.sh               # Service startup script
```

## Services

### SmartSolar
Collects data from Victron SmartSolar charge controllers via Bluetooth Low Energy (BLE). Stores data locally and provides a web dashboard.

### Shelly
Monitors Shelly energy monitoring devices via Bluetooth, collecting power consumption and energy usage data.

### Telegraf
Syncs collected data to InfluxDB Cloud with offline buffering capabilities. Handles intermittent connectivity gracefully.

### Cloudflared (Optional)
Provides secure remote access to your services via Cloudflare Tunnel without opening ports on your network. Uses the `erisamoe/cloudflared` image for ARMv6 compatibility with Raspberry Pi Zero W. See [cloudflared/README.md](cloudflared/README.md) for setup instructions.

## Troubleshooting

### "No Victron devices found"
- Ensure Bluetooth is enabled on your device
- Check if the SmartSolar device is in range
- Verify "Instant Readout" is enabled in VictronConnect

### "No encryption key found"
- Add your device's encryption key using one of the methods above
- Verify the MAC address matches exactly (case-insensitive)

### "Could not parse Victron data"
- Ensure you have the correct encryption key
- Try re-copying the key from VictronConnect
- Check if your device firmware is up to date

## Environment Variables

- `SMARTSOLAR_KEY_<MAC>`: (Optional) Device encryption key (MAC with underscores)
- `SMARTSOLAR_TARGET_DEVICE`: (Optional) Target specific device for debugging
- `BLE_SCAN_TIMEOUT`: (Optional) Maximum seconds to scan for BLE device (1-30, default: 5)
- `COLLECTION_INTERVAL`: (Optional) Seconds between data collections (min: 10, default: 60)
- `TZ`: (Optional) Timezone (default: UTC)

## Data Export

The system stores data in JSON format, making it easy to:
- Export to InfluxDB or other time-series databases
- Process with Python scripts
- Integrate with home automation systems

## Contributing

Pull requests are welcome! Please test with your Victron device and include:
- Device model
- Firmware version
- Any issues encountered

## License

This project is provided "as-is" without warranty. It is not officially supported by Victron Energy.

## Acknowledgments

- Built using the [victron-ble](https://github.com/keshavdv/victron-ble) library
- Thanks to the Victron community for protocol documentation 

## Roadmap

- [x] Basic BLE data collection
- [x] Web dashboard
- [x] Encryption key management
- [x] Export to InfluxDB Cloud
- [ ] Multi-device support improvements
- [ ] Historical data visualization
- [ ] Alerts and notifications
- [ ] Data export utilities 
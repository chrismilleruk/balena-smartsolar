# Telegraf InfluxDB Cloud Sync

This service syncs SmartSolar data to InfluxDB Cloud with support for intermittent connectivity.

## Features

- **Real-time streaming**: When connected, data is sent with <5 minute lag
- **Persistent buffering**: Stores up to 500MB of data during disconnections
- **Automatic catch-up**: Syncs historical data when connection is restored
- **State tracking**: Remembers file positions across restarts
- **No data loss**: Handles disconnections up to 7 days

## Configuration

Set these environment variables in Balena Cloud:

### Required Variables

- `INFLUX_TOKEN`: Your InfluxDB Cloud API token
- `INFLUX_ORG`: Your InfluxDB organization name
- `INFLUX_BUCKET`: Bucket name (default: `smartsolar`)

### Optional Variables

- `INFLUX_URL`: InfluxDB Cloud URL (default: `https://us-east-1-1.aws.cloud2.influxdata.com`)
  - US East: `https://us-east-1-1.aws.cloud2.influxdata.com`
  - EU Central: `https://eu-central-1-1.aws.cloud2.influxdata.com`
  - US West: `https://us-west-2-1.aws.cloud2.influxdata.com`

## Data Format

The service expects NDJSON files (one JSON object per line) in `/data/smartsolar-v1/`:

```json
{"timestamp":"2025-05-25T23:13:07.914587+00:00","device_name":"SmartSolar HQ22189Q3QF","device_address":"DF:C9:B0:6E:3F:EF","parsed_data":{"battery_voltage":12.34,"solar_power":0,...}}
```

## Migration from JSON Arrays

If you have existing JSON array files, run the migration script:

```bash
python /usr/src/app/migrate_to_ndjson.py
```

This converts files from:
```json
[
  {"timestamp": "...", ...},
  {"timestamp": "...", ...}
]
```

To NDJSON format:
```json
{"timestamp": "...", ...}
{"timestamp": "...", ...}
```

## Monitoring

### Check Telegraf Status

```bash
# View logs
balena logs telegraf

# Check buffer status
docker exec telegraf_container telegraf --test

# View state files
ls -la /var/lib/telegraf/tail_state/
```

### InfluxDB Query Examples

```flux
// Last 24 hours of battery voltage
from(bucket: "smartsolar")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "smartsolar")
  |> filter(fn: (r) => r._field == "battery_voltage")
  |> filter(fn: (r) => r.device_name == "SmartSolar HQ22189Q3QF")
```

## Troubleshooting

### No data appearing in InfluxDB

1. Check environment variables are set correctly
2. Verify network connectivity: `curl -I https://us-east-1-1.aws.cloud2.influxdata.com/health`
3. Check Telegraf logs: `balena logs telegraf --tail 100`
4. Verify files exist: `ls -la /data/smartsolar-v1/*.ndjson`

### Data gaps after reconnection

- Telegraf will automatically catch up when connection is restored
- Check buffer directory size: `du -sh /var/lib/telegraf/buffer/`
- Increase buffer size in `telegraf.conf` if needed

### High memory usage

- Reduce `metric_buffer_limit` in `telegraf.conf`
- Ensure old data files are being cleaned up

## Architecture

```
SmartSolar App → NDJSON Files → Telegraf → InfluxDB Cloud
                                    ↓
                            Persistent State
                            (survives restarts)
```

The system maintains three types of state:
1. **Tail state**: Current position in each file
2. **Buffer state**: Unsent metrics during disconnections  
3. **File state**: Which files have been fully processed

This ensures no data loss even with extended disconnections or device restarts.

## ARM v6 Support (Raspberry Pi Zero W)

The standard Telegraf Docker image doesn't support ARM v6 architecture. For Raspberry Pi Zero W, you have three options:

### Option 1: Use the ARM v6 Dockerfile (Recommended for Docker)

The included `Dockerfile` uses the official ARM binary (armel) which supports ARM v6:

```bash
# Build and deploy normally
balena push <your-app-name>
```

### Option 2: Install Telegraf on Host OS

If Docker build fails, you can install Telegraf directly on the Balena host OS:

```bash
# SSH into your device
balena ssh <device> 

# Run the installation script from the smartsolar container
docker exec -it smartsolar_container bash
cd /usr/src/app
chmod +x telegraf/install-on-host.sh
./telegraf/install-on-host.sh
```

### Option 3: Build from Source

Use `Dockerfile.armv6` to build Telegraf from source (slower but guaranteed compatibility):

```bash
# In docker-compose.yml, change:
telegraf:
  build: 
    context: ./telegraf
    dockerfile: Dockerfile.armv6
```

### Verification

After deployment, verify Telegraf is running:

```bash
# If using Docker
balena logs telegraf

# If installed on host
sudo systemctl status telegraf
sudo journalctl -u telegraf -f
``` 
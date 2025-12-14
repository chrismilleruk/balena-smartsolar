# Power Management System

This system implements coordinated power management to reduce idle power consumption from **80mA** to approximately **40-50mA** (37-50% reduction).

## Power Savings Breakdown

| Strategy | Current Draw Reduction | Percentage Savings |
|----------|----------------------|-------------------|
| WiFi Management | 10-20mA | 12-25% |
| Service Lifecycle | 15-25mA | 18-30% |
| CPU Frequency Scaling | 10-20mA | 12-25% |
| **Combined Total** | **25-40mA** | **31-50%** |

## Components

### 1. `wifi-power-mgmt.sh`
- Disables WiFi radio between upload windows (every 6 hours)
- Saves ~15mA continuously
- Automatically reconnects for uploads

### 2. `service-manager.sh`  
- Stops non-essential Docker containers during sleep
- Keeps only BLE data collection active
- Saves ~20mA by stopping web UI, CloudFlare, etc.

### 3. `cpu-scaling.sh`
- Reduces CPU frequency to minimum during idle periods
- Scales up for BLE operations and uploads
- Saves ~15mA during sleep cycles

### 4. `power-scheduler.py`
- Master coordinator that orchestrates all power strategies
- Manages sleep/wake/upload cycles
- Provides logging and error handling

## Usage

### Manual Testing
```bash
# Test WiFi management
./wifi-power-mgmt.sh disable  # Save ~15mA
./wifi-power-mgmt.sh enable   # Re-enable for uploads

# Test CPU scaling  
./cpu-scaling.sh powersave    # Save ~15mA
./cpu-scaling.sh performance  # Restore for operations
./cpu-scaling.sh status       # Check current state

# Test service management
./service-manager.sh sleep    # Stop non-essential services
./service-manager.sh wake     # Restart all services
```

### Production Deployment
```bash
# Run the master power scheduler
python3 power-scheduler.py
```

## Integration with Existing System

The power scheduler works alongside your existing services:
- **SmartSolar**: Continues BLE collection on schedule
- **Shelly**: Continues BLE collection on schedule  
- **Telegraf**: Only runs during upload windows
- **Web UI**: Only available during upload windows (or on-demand wake)

## Expected Results

**Before**: 80mA × 24h = 1.92Ah/day  
**After**: 45mA × 24h = 1.08Ah/day  
**Savings**: 0.84Ah/day (44% reduction)

This extends battery life significantly and reduces heat generation on the Pi Zero W.

## Monitoring

Logs are written to:
- `/data/logs/power-scheduler.log` - Master scheduler events
- `/data/logs/power-mgmt.log` - WiFi management events  
- `/data/logs/service-mgmt.log` - Service lifecycle events
- `/data/logs/cpu-scaling.log` - CPU frequency changes

## Safety Features

- Graceful fallbacks on script failures
- Automatic service recovery
- Upload window guarantees (every 6 hours)
- Error logging and monitoring
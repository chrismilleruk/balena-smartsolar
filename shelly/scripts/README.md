# Shelly Scripts

This directory contains documentation and utilities for configuring the Shelly Plus Uni device.

## Hybrid Scheduling Setup

We use native Shelly features for WiFi scheduling:
- **Native Schedules**: Turn WiFi ON at specific times (configured via web UI)
- **Auto-off Timer**: Automatically turn OFF after 5 minutes
- **Manual Override**: Disable/enable auto-off for manual control

See `hybrid_scheduler_setup.md` for detailed setup instructions.

## Key Discoveries

- The Shelly auto-off timer can be reset by turning an already-ON switch ON again
- Timer status is available via `timer_started_at` and `timer_duration` fields
- No scripting needed - native features are more reliable

## Configuration via Web UI

1. **Set up schedules** (12:00, 13:00, etc.)
2. **Enable Auto-off** timer (300 seconds)
3. **Manual override** by toggling auto-off setting

## Monitoring

The Python container monitors the Shelly device via BLE and logs:
- Switch state (ON/OFF)
- Timer status (remaining time)
- Battery voltage
- Device temperature 
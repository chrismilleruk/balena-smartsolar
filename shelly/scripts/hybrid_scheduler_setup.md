# Hybrid WiFi Scheduling Setup

This document describes how to set up WiFi scheduling using native Shelly features combined with Auto-off timer control. This approach is simpler and more reliable than scripting.

## Overview

The hybrid approach uses:
1. **Native Shelly Schedules** - To turn WiFi ON at specific times
2. **Auto-off Timer** - To automatically turn WiFi OFF after 5 minutes
3. **Manual Override** - Disable/enable Auto-off timer for manual control

## Setup Instructions

### Step 1: Configure Auto-off Timer

1. Access Shelly Web UI at http://192.168.11.253
2. Go to **Switch 0** settings
3. Enable **Timer** → **Auto OFF**
4. Set timer to **300 seconds** (5 minutes)
5. Save settings

### Step 2: Create Schedules

For each hour you want WiFi to turn on (12:00-22:00):

1. Go to **Schedules** section
2. Click **Add Schedule**
3. Configure:
   - **Name**: "WiFi Hour XX:00" (e.g., "WiFi Hour 12:00")
   - **Enable**: Yes
   - **Time**: Set to XX:00 (e.g., 12:00)
   - **Days**: Select all days (or specific days as needed)
   - **Action**: Switch 0 → Turn ON
4. Save schedule

Repeat for hours: 12:00, 13:00, 14:00, 15:00, 16:00, 17:00, 18:00, 19:00, 20:00, 21:00

### Step 3: Test the Setup

1. Wait for the next scheduled hour
2. Verify Switch 0 turns ON at XX:00
3. Verify Switch 0 turns OFF at XX:05 (5 minutes later)

## Manual Override via Bluetooth

To enter manual mode (disable automatic OFF):

```python
# Disable Auto-off (manual mode)
await client.call_rpc("Switch.SetConfig", {
    "id": 0,
    "config": {"auto_off": False}
})

# Re-enable Auto-off (return to scheduled mode)
await client.call_rpc("Switch.SetConfig", {
    "id": 0,
    "config": {"auto_off": True, "auto_off_delay": 300}
})
```

## Manual Override via Web UI

1. Go to Switch 0 settings
2. Disable "Auto OFF" timer
3. Save (device is now in manual mode)
4. To return to scheduled mode: Enable "Auto OFF" timer, set to 300 seconds, Save

## Advantages of This Approach

1. **No scripting required** - Uses native Shelly features
2. **Survives reboots** - Settings are persistent
3. **Easy to modify** - Change schedules via Web UI
4. **Manual override** - Simple on/off toggle for Auto-off timer
5. **Lower resource usage** - No script running continuously

## Schedule Summary

| Time  | Action | Auto-off |
|-------|--------|----------|
| 12:00 | ON     | OFF at 12:05 |
| 13:00 | ON     | OFF at 13:05 |
| 14:00 | ON     | OFF at 14:05 |
| 15:00 | ON     | OFF at 15:05 |
| 16:00 | ON     | OFF at 16:05 |
| 17:00 | ON     | OFF at 17:05 |
| 18:00 | ON     | OFF at 18:05 |
| 19:00 | ON     | OFF at 19:05 |
| 20:00 | ON     | OFF at 20:05 |
| 21:00 | ON     | OFF at 21:05 |

## Monitoring

The Python container will monitor and log:
- Current switch state (ON/OFF)
- Auto-off timer status
- Manual overrides
- Battery voltage
- Device temperature

All scheduling logic remains on the Shelly device. 
# Shelly Timer Behavior Notes

## Key Discoveries

### Timer Detection
The Shelly Plus Uni doesn't provide a `timer_remaining` field. Instead, when auto-off is active, it provides:
- `timer_started_at`: Unix timestamp when the timer started
- `timer_duration`: Total duration of the timer in seconds (e.g., 300 for 5 minutes)

To calculate remaining time:
```python
remaining = timer_duration - (current_time - timer_started_at)
```

### Timer Reset Behavior
**Important**: Turning ON an already-ON switch resets the timer to full duration!
- This is useful for extending WiFi time without disabling auto-off
- Each ON command restarts the countdown from the beginning

### Manual Mode Detection
- If `timer_started_at` is NOT present in the status → Auto-off is disabled (manual mode)
- If `timer_started_at` IS present → Auto-off timer is active and counting down

## Practical Applications

### 1. Hybrid Scheduling Approach
- Use native Shelly schedules to turn WiFi ON at specific times
- Use Auto-off timer (5 minutes) to turn OFF automatically
- Manual override by disabling/enabling auto-off via BLE

### 2. Timer Extension
Instead of disabling auto-off for manual connections, we can:
```python
# Simply turn the switch ON again to reset timer to 5 minutes
await client.call_rpc("Switch.Set", {"id": 0, "on": True})
```

### 3. Smart Override Detection
Monitor for:
- Switch ON outside scheduled hours → Manual intervention
- Auto-off disabled via web UI → Manual mode activated
- Active SSH sessions or system updates → Extend timer

## RPC Methods Summary

```python
# Get current status (includes timer info)
await client.call_rpc("Switch.GetStatus", {"id": 0})

# Turn switch ON (resets timer if already ON)
await client.call_rpc("Switch.Set", {"id": 0, "on": True})

# Get/Set auto-off configuration
await client.call_rpc("Switch.GetConfig", {"id": 0})
await client.call_rpc("Switch.SetConfig", {
    "id": 0,
    "config": {
        "auto_off": True,
        "auto_off_delay": 300  # seconds
    }
})
```

## Test Scripts Created
- `test_autooff_control.py` - Configure auto-off settings
- `test_timer_detection.py` - Monitor and test timer behavior
- `manual_override_handler.py` - Handle manual interventions
- `integration_example.py` - Integration patterns

## Next Steps for Implementation
1. Set up Shelly schedules via web UI (12:00-22:00 hourly)
2. Enable Auto-off timer (300 seconds)
3. Deploy monitoring container to track state
4. Implement smart override detection for manual connections
5. Test complete system before boat installation 
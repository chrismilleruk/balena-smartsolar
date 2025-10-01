# Power Loss Investigation - October 1, 2025

## Issue
Missing data periods in marine battery monitoring system during September 2025.

## Investigation Summary
- **Missing periods**: September 8-12 (5 days) and September 17-23 (7 days)
- **Root cause**: Complete system power loss during severe battery undervoltage events
- **Confirmation method**: system_stats uptime analysis showing fresh reboots after gaps

## Key Findings
1. Monitoring system powered by same battery it monitors
2. System shutdown occurs around 8.4V battery voltage
3. No local data exists for missing periods - system was completely offline
4. Data gaps are real and cannot be recovered

## Data Files
- `Domestic Voltage Trend Oct 1 2025.csv` - Primary battery voltage analysis
- `Engine Voltage Trend Oct 1 2025.csv` - Secondary battery voltage analysis

## SQL Query Used
```sql
SELECT 
  DATE_TRUNC('day', time) AS day,
  MIN(uptime) AS min_uptime,
  MAX(uptime) AS max_uptime,
  COUNT(*) AS readings
FROM "system_stats"
WHERE time >= '2025-09-01T00:00:00Z' AND time <= '2025-10-01T23:59:59Z'
GROUP BY DATE_TRUNC('day', time)
ORDER BY day
```

## Power Loss Timeline
- **Sept 7, 05:05**: Last system activity (uptime 209,118s)
- **Sept 8-12**: Complete power outage (no system_stats data)
- **Sept 13, 12:05**: System recovery (uptime 288s = fresh reboot)
- **Sept 16**: Another crash and power loss
- **Sept 17-23**: Second complete outage period
- **Sept 25**: System restored again

## Recommendations
- Consider backup power or low-voltage shutdown protection
- Monitor critical voltage thresholds (8.4V shutdown, 11V+ stable)
- Use uptime analysis for future power loss investigations
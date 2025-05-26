# Telegraf Development Tools

This directory contains tools for testing and developing the Telegraf configuration locally.

## Files

- `test-config.sh` - Script to download Telegraf and validate configuration
- `telegraf-test.conf` - Test configuration that outputs to stdout
- `test-data.ndjson` - Sample data in NDJSON format for testing

## Testing Configuration

Before deploying, test the configuration locally:

```bash
cd dev
./test-config.sh
```

This will:
1. Download the appropriate Telegraf binary for your OS
2. Validate the main configuration file
3. Show available plugins

## Testing Data Parsing

To test how Telegraf parses your data:

```bash
cd dev
./telegraf --config telegraf-test.conf --once
```

This reads `test-data.ndjson` and outputs the parsed metrics to stdout.

## Adding Test Data

Edit `test-data.ndjson` to add more test cases. Each line should be a valid JSON object matching the format your application produces:

```json
{"timestamp":"2025-05-26T06:50:00.000000+00:00","device_name":"SmartSolar HQ22189Q3QF","device_address":"DF:C9:B0:6E:3F:EF","parsed_data":{...}}
```

## Notes

- The test configuration uses `watch_method = "poll"` for compatibility
- Output goes to stdout for easy inspection
- The telegraf binary is gitignored and downloaded on demand 
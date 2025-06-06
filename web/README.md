# Connectivity Check Service

A simple web service that displays QR codes and checks connectivity for marine services.

## Features

- **Automatic Network Detection**: Detects whether you're on the local boat network or accessing via VPN/Internet
- **QR Codes**: Generates QR codes for each service URL for easy mobile access
- **Live Connectivity Check**: Shows real-time status of each service
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Auto-refresh**: Automatically checks connectivity every 30 seconds

## Services Monitored

- Navigation (OpenCPN)
- Router (GL.iNet)
- AIS
- SignalK
- InfluxDB
- Dashboard

## Access

- **Local Network**: http://192.168.10.200 (or the IP of your Balena device)
- **Remote Access**: Through your Cloudflare tunnel URL

## How It Works

1. The service detects if you're on the local network by trying to reach the router at 192.168.10.1
2. Based on network detection:
   - **Local Network**: Uses direct IP addresses (http://192.168.10.x:port)
   - **Remote Access**: Uses Cloudflare tunnel URLs (https://service.irl5795.net)
3. QR codes are generated dynamically for the appropriate URLs
4. Connectivity is checked in parallel for all services

## Configuration

Service definitions are in `app.py`. To add or modify services, update the `SERVICES` list. 
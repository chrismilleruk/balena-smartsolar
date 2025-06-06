# Cloudflared Service

This service runs Cloudflare Tunnel (cloudflared) to securely expose your services to the internet without opening ports.

## Compatibility

This service uses the `erisamoe/cloudflared` Docker image which supports multiple architectures including:
- AMD64 (x86_64)
- ARM64 (aarch64)
- ARMv7 (arm/v7)
- ARMv6 (arm/v6) - **Compatible with Raspberry Pi Zero W**
- 386 (x86)
- s390x (IBM Z)
- ppc64le

Note: We use this image instead of the official Cloudflare image because the official image doesn't support ARMv6, which is required for Raspberry Pi Zero W.

## Configuration

### Prerequisites

1. A Cloudflare account
2. A domain managed by Cloudflare
3. A configured Cloudflare Tunnel

### Setting up a Cloudflare Tunnel

1. Log in to the [Cloudflare Zero Trust dashboard](https://one.dash.cloudflare.com/)
2. Navigate to Networks > Tunnels
3. Click "Create a tunnel"
4. Choose "Cloudflared" as the connector type
5. Name your tunnel (e.g., "balena-marine-monitor")
6. Save the tunnel token that is generated

### Balena Configuration

Add the following environment variable to your Balena device:

- `TUNNEL_TOKEN`: The tunnel token from Cloudflare (required)

You can set this via:
- Balena Cloud dashboard: Device > Device Variables
- Balena CLI: `balena env add TUNNEL_TOKEN "your-token-here" --device <device-uuid>`

### Configuring Tunnel Routes

After the tunnel is running, configure routes in the Cloudflare dashboard:

1. Go to your tunnel in the Zero Trust dashboard
2. Click "Configure"
3. Add public hostname routes, for example:
   - `smartsolar.yourdomain.com` → `http://localhost:8081` (for the SmartSolar web dashboard)
   - `metrics.yourdomain.com` → `http://localhost:49312` (for Telegraf metrics)

Note: Since we're using `network_mode: host`, services are accessible via localhost.

### Security Considerations

- The tunnel token should be kept secret
- Use Cloudflare Access policies to add authentication if needed
- Consider which services should be exposed publicly

## Troubleshooting

### Tunnel not connecting

1. Check the logs: `balena logs cloudflared`
2. Verify the TUNNEL_TOKEN is set correctly
3. Ensure the device has internet connectivity

### Service not accessible

1. Verify the tunnel is showing as "Healthy" in Cloudflare dashboard
2. Check that routes are configured correctly
3. Ensure the target service is running and accessible locally

## Resources

- [Cloudflare Tunnel documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Zero Trust dashboard](https://one.dash.cloudflare.com/) 
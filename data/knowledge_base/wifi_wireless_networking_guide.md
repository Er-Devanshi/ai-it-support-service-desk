# Wi-Fi and Wireless Networking Troubleshooting Guide

## Overview
This guide provides standard operating procedures for resolving Wi-Fi connectivity issues in the corporate environment.

## Wireless Connection Troubleshooting

### Unable to Connect to Corporate Wi-Fi Network
- Steps:
  1. Restart your device and the Wi-Fi router.
  2. Forget the network from your device settings and reconnect.
  3. Verify Airplane Mode is OFF in your device settings.
  4. Move closer to the Wi-Fi router to check signal strength.
  5. Check if other devices can connect — if not, the issue may be with the router itself.
  6. If the issue persists, contact IT support with your device MAC address.

### Intermittent Wi-Fi Drops
- Cause: Signal interference, low battery mode, or driver issues.
- Steps:
  1. Check available disk space and memory on your device.
  2. Update Wi-Fi adapter drivers to the latest version from the manufacturer.
  3. Disable power-saving mode in Wi-Fi adapter settings.
  4. Enable 5GHz band if available (less interference than 2.4GHz).
  5. Reduce interference by moving away from microwave ovens and cordless phones.

### Slow Wi-Fi Speed
- Steps:
  1. Run a speed test to compare against corporate baseline (contact IT for expected speeds).
  2. Reduce the number of connected devices on your Wi-Fi network.
  3. Reposition yourself closer to the router.
  4. Check for router firmware updates and apply if available.
  5. If speed remains below baseline, submit a ticket to IT Network Engineering.

### Cannot Authenticate (Login Failed)
- Steps:
  1. Verify your domain username and password are correct.
  2. Ensure your device has a valid machine certificate installed (Windows: `certmgr.msc`).
  3. Check if your device is joined to the corporate Active Directory domain.
  4. Renew the device DHCP lease: run `ipconfig /release` then `ipconfig /renew` (Windows Command Prompt).
  5. Clear the Wi-Fi network cache and re-authenticate.

## Network Diagnostics

### Testing Connectivity
- Ping a reliable internal resource: `ping intranet.company.local`
- Flush DNS cache: `ipconfig /flushdns` (Windows)
- Obtain network configuration details: `ipconfig /all` (Windows)

### Escalation Criteria
- Escalate to IT Network Engineering if entire team cannot connect.
- Escalate if signal strength is less than -70 dBm (very weak).
- Escalate if speed is less than 25% of corporate baseline.

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

### Wi-Fi Connection Intermittent or Dropping

**Symptoms:**
- Wi-Fi disconnects and reconnects frequently
- Internet connection is unstable or drops for a few seconds then returns
- Device loses Wi-Fi signal periodically even when router is nearby

**Step-by-step resolution:**

1. **Check for interference sources.** Move away from cordless phones, microwave ovens, or other devices operating on the 2.4 GHz band. These devices can interfere with Wi-Fi signals.

2. **Enable the 5 GHz band if available.** 5 GHz is less congested than 2.4 GHz. In your Wi-Fi settings, look for networks with "5G" in the name or manually select the 5 GHz option in your Wi-Fi adapter settings. This band has more channels and experiences less interference.

3. **Disable power-saving mode on your Wi-Fi adapter.** Power saving can cause the adapter to lower power and lose signal intermittently. In Windows: Device Manager → Network Adapters → right-click your Wi-Fi adapter → Properties → Power Management tab → uncheck "Allow the computer to turn off this device to save power".

4. **Update your Wi-Fi adapter drivers.** Outdated drivers can cause connection instability. In Windows: Device Manager → Network Adapters → right-click → Update driver → Search automatically for updated driver software. On macOS, check System Preferences → Network for any available system updates.

5. **Move closer to the Wi-Fi router.** Signal strength decreases with distance and through walls. Test by moving closer to the router. If the connection is stable closer by, consider positioning the router more centrally or moving to a location with better signal.

6. **Restart your router.** Power cycle the router by unplugging it for 10 seconds, then plugging it back in. Wait for all lights to stabilize (usually 1–2 minutes) before reconnecting.

7. **Check your device's Wi-Fi connection history.** If your device is trying to auto-connect to multiple networks, this can cause drops. In Windows Settings → Network & Internet → Wi-Fi → Manage known networks, remove any networks you no longer use.

**Escalation:** If the connection remains unstable after all steps, or if the entire team is experiencing drops, escalate to IT Network Engineering with details of your device type, router location, and when the issue started.

### Finding the Corporate Wi-Fi Network Name (SSID)

**Symptoms:**
- You cannot find your company's Wi-Fi network in the available networks list
- You are unsure which network is the official corporate network
- Multiple similar networks appear and you do not know which one to join

**Step-by-step resolution:**

1. **Check the IT Self-Service Portal or internal IT wiki.** Your company's official Wi-Fi SSID (network name) is listed in the IT portal, company intranet, or IT documentation. Log in and search for "Wi-Fi SSID", "Network Name", or "Wireless Setup".

2. **Ask your IT helpdesk or team lead.** The official SSID can be provided by [contact IT Helpdesk]. Have your employee ID ready and confirm you are setting up a corporate-managed device.

3. **Look for a network with your company name or recognizable branding.** Many organizations use their company name or abbreviation in the SSID (for example, "CompanyName-WiFi" or "ACME-Office"). If multiple networks have similar names, verify which one is correct with IT before connecting.

4. **Do not connect to unknown or guest networks unless instructed.** Connecting to an unsecured or unrecognized network may expose your device to security risks. Always confirm the official SSID with IT.

5. **Verify you are on the correct network after connecting.** Once connected, open a browser and you should be able to reach internal company websites (if applicable) and have general internet access. If access is limited, reconnect with the correct SSID.

**When to escalate:** If you cannot locate the official SSID through the IT portal or internal resources, or if you are unsure whether a network is legitimate, contact [contact IT Helpdesk]. Do not attempt to connect to networks you cannot verify.

## Network Diagnostics

### Testing Connectivity
- Ping a reliable internal resource: `ping intranet.company.local`
- Flush DNS cache: `ipconfig /flushdns` (Windows)
- Obtain network configuration details: `ipconfig /all` (Windows)

### Escalation Criteria
- Escalate to IT Network Engineering if entire team cannot connect.
- Escalate if signal strength is less than -70 dBm (very weak).
- Escalate if speed is less than 25% of corporate baseline.

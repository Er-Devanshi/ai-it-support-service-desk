# Corporate VPN and Remote Access Troubleshooting Guide

## Overview
This operational handbook provides tier-1 and tier-2 IT support engineers and employees with standard operating procedures for diagnosing and resolving Virtual Private Network (VPN) connection failures.

## Common Error Codes and Resolutions

### Error 412: The remote peer is no longer responding
- Cause: Network timeout or ISP packet dropping along the route.
- Steps:
  1. Verify local internet connectivity by browsing to an external website.
  2. Disconnect from guest or public Wi-Fi networks that block IPsec/UDP port 500/4500.
  3. Toggle the VPN client protocol from IPsec (IKEv2) to SSL/TLS (TCP 443) in client settings.
  4. Restart your home router and wait 60 seconds before reconnecting.

### Error 442: Failed to enable Virtual Adapter
- Cause: Conflicting network filter drivers or disabled virtual network adapter.
- Steps:
  1. Open Windows Device Manager (press Win + X, select Device Manager).
  2. Expand 'Network adapters' and locate the Cisco AnyConnect / GlobalProtect Virtual Adapter.
  3. If marked with an exclamation point, right-click and choose 'Enable device'.
  4. If disabled, run the Windows Network Adapter troubleshooter.
  5. Restart the Cisco AnyConnect Secure Mobility Agent service in `services.msc`.

### Multi-Factor Authentication (MFA) Push Timeout
- Cause: Phone notification delay, clock drift, or out-of-sync authenticator tokens.
- Steps:
  1. Ensure your smartphone has active cellular or Wi-Fi data.
  2. Open the authenticator app manually and enter the 6-digit rolling code instead of relying on push notifications.
  3. Verify your smartphone date and time settings are set to 'Automatic / Network Provided'.
  4. If your device was recently upgraded, submit an MFA Token Re-enrollment request in the IT portal.

## Split Tunneling Rules
- Work-related internal services (internal wikis, code repositories, ERP, JIRA) route strictly through the encrypted corporate VPN tunnel.
- High-bandwidth public services (YouTube, Spotify, personal cloud storage) bypass the tunnel directly via local internet breakout to conserve corporate bandwidth.

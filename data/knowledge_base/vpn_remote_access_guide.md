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

## VPN Requirements for Remote Work

**When VPN connection is required:**
- When accessing company resources (email, file shares, internal applications) from outside the corporate office or corporate network
- When connecting from home, a coffee shop, hotel, airport, or any public Wi-Fi network
- When using a mobile device to access company services from outside the office
- When you need to connect to a company database, internal application server, or restricted resource

**When VPN may not be required:**
- When accessing publicly available company websites (check your IT policy)
- When using company-approved cloud services that do not require VPN (some SaaS applications allow direct connection)

**To verify your company's VPN policy:** Check the IT Self-Service Portal, company intranet, or contact [contact IT Helpdesk] for your organization's specific remote access and VPN requirements. VPN policies vary by company, department, and resource sensitivity.

**Step-by-step VPN connection:**
1. Download and install the official VPN client provided by [contact IT Helpdesk] or available on the IT portal.
2. Open the VPN client and enter your corporate username and password.
3. If prompted, complete multi-factor authentication (MFA) on your registered device.
4. Once connected, you should see a "Connected" status in the VPN client.
5. You can now access corporate resources as if you were in the office.
6. When finished, disconnect from the VPN by clicking "Disconnect" in the client.

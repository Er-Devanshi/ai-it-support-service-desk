# Multi-Factor Authentication (MFA) Troubleshooting Guide

## Overview
This guide assists employees and IT support with MFA setup and troubleshooting.

## Setting Up MFA for the First Time

### Microsoft Authenticator Setup (Recommended)
- Steps:
  1. Download Microsoft Authenticator from your app store (iOS/Android/Windows).
  2. Log into your account on the IT portal and navigate to Security > MFA Setup.
  3. Select "Authenticator App" as your MFA method.
  4. Scan the QR code using the Microsoft Authenticator app.
  5. Verify by entering the 6-digit code displayed in the app.
  6. Save the backup codes in a secure location (never share these codes).

### SMS and Email Backup Methods
- If you lose access to your authenticator app, SMS or email codes can serve as backup.
- Register both methods in your account to ensure resilience.

## MFA Authentication Failures

### "Code Has Expired" Error
- Cause: The 6-digit code is time-sensitive and expires after 30 seconds.
- Steps:
  1. Use the authenticator app to generate a fresh 6-digit code.
  2. Enter the new code quickly within the 30-second window.
  3. Ensure your device's date and time are set to automatic (network-synchronized).

### Authenticator App Not Generating Codes
- Cause: Clock drift on your device or corrupted app cache.
- Steps:
  1. Verify your device's date and time are set to automatic/network time.
  2. Restart your device completely.
  3. Uninstall and reinstall the Microsoft Authenticator app.
  4. Re-add your account by scanning the QR code again.

### Lost Access to Authenticator App
- If your authenticator device is lost, stolen, or malfunctioning:
  1. Use a previously saved backup code to log in.
  2. Navigate to your account settings and disable the broken MFA method.
  3. Set up a new authenticator device immediately.
  4. Contact IT Security to audit your account for unauthorized access.

### Push Notification Not Appearing
- Cause: Network connectivity issue or notification permissions disabled.
- Steps:
  1. Ensure your phone has active cellular or Wi-Fi internet connectivity.
  2. Check that notification permissions are enabled for Microsoft Authenticator in app settings.
  3. Manually enter the 6-digit code from the authenticator app instead of waiting for push notification.
  4. If the issue persists, restart the app and your phone.

## MFA and VPN Conflicts

### MFA Not Triggering When Connecting to VPN
- VPN access may require MFA but the notification may be delayed.
- Steps:
  1. After entering your credentials in the VPN client, wait up to 60 seconds for the MFA prompt.
  2. Check your authenticator app manually for incoming code requests.
  3. Manually enter the 6-digit code if the push notification doesn't arrive.
  4. Ensure your VPN client is updated to the latest version.

## Security Best Practices

- Never share your MFA codes or backup codes with anyone, including IT staff.
- Never respond to unsolicited text messages or emails asking for MFA codes.
- Review your account login history monthly in the IT portal to detect unauthorized access.
- Enable MFA immediately after creating your corporate account.

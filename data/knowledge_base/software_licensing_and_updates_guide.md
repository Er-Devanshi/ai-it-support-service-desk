# Software Licensing and Updates Troubleshooting Guide

## Overview
This guide covers issues with software licensing, application updates, crashes, and document signing tools. Follow each section for step-by-step resolution.

## Software License Expired

**Symptoms:**
- Application displays "License has expired" or "Activate your product" message
- Cannot open or use the software; it only shows a license screen
- Features are disabled or limited due to expired license
- Application stops working or goes into trial mode

**Step-by-step resolution:**

1. **Note the application name and license type.** Check if the license is personal, site (shared across your organization), or subscription. This information is usually in the application's "Help" → "About" menu or Licensing Information window.

2. **Check the IT Self-Service Portal for license renewal.** Go to the IT portal and look for a "Software Licenses" or "License Renewal" section. Some licenses can be renewed by employees directly; others require IT approval.

3. **If the license can be renewed in the portal, follow the renewal process.** You may need to provide your business justification or manager approval. The renewed license key will be emailed to you or made available immediately.

4. **For application-based licenses, re-enter the license key.** If the portal provides a new license key, open the application and go to "Help" → "Licensing" or "Activate" → "Enter License Key" and paste the new key. The application should recognize the license immediately.

5. **For subscription-based software, verify your subscription status.** Log in to your personal account within the application (or on the vendor's website) and confirm your subscription is active. If billing failed, update your payment method or contact your subscription provider.

6. **Request a temporary license extension if renewal is pending.** If your license is expired but the renewal has been submitted, contact [contact IT Helpdesk] and ask if they can provide a temporary license key to keep you productive while the official renewal is processed.

7. **If you no longer need the software, request de-activation.** Some licenses are limited per organization. If the software is no longer needed for your role, request deactivation through IT so the license can be reassigned to another employee. This frees up a license slot.

**Escalation:** If you requested a license renewal and it has been more than 2 business days without a response, follow up with [contact IT Helpdesk]. Provide your request ticket number and the application name.

## Software Update Failing or Installation Error

**Symptoms:**
- Update download starts but fails partway through
- Error message: "Update failed", "Installation error", or specific error code
- Update completes but application does not launch after updating
- Stuck on "Checking for updates" or download percent does not advance

**Step-by-step resolution:**

1. **Check your internet connection.** Ensure you are connected to the corporate network or VPN (if working remotely). Try opening a web browser to confirm internet access. Slow or intermittent connections can interrupt updates.

2. **Free up disk space.** Updates require space to download and install. Go to Windows Settings → System → Storage and check available disk space. If less than 2 GB is available, delete unnecessary files or clean temporary files using Disk Cleanup.

3. **Disable antivirus temporarily.** Antivirus software can interfere with updates. Temporarily disable your antivirus (or add the application folder to the antivirus exclusion list) while updating. Restart the update.

4. **Restart your computer and try updating again.** Close all applications, restart your computer, and immediately attempt the update again. Sometimes temporary processes prevent updates from completing.

5. **Update manually if automatic update fails.** Download the latest installer from the application vendor's official website (ask [contact IT Helpdesk] for the approved source). Close the application completely, run the installer, and follow the on-screen steps. This often succeeds where automatic updates fail.

6. **Uninstall and reinstall the application.** If manual update still fails, uninstall the old version completely: Windows → Control Panel → Uninstall a program → find the application → Uninstall. Restart your computer, then download and install the latest version fresh.

7. **Check for account permissions.** Some applications require admin rights to update. If you see a "Permission Denied" error, ask your IT department to run the update for you or to grant temporary admin rights to your account.

**Escalation:** If the update fails multiple times even after manual installation and restart, submit a ticket to [contact IT Helpdesk] with the application name, version number, error code, and what steps you have already tried. Provide screenshots of error messages if available.

## Application Crashes or Closes on Launch

**Symptoms:**
- Application starts but immediately closes or crashes
- Application opens briefly then shows "has stopped working"
- Error message appears: "Runtime error", "Unexpected error", or "Fatal exception"
- Application hangs or freezes on the splash screen

**Step-by-step resolution:**

1. **Restart your computer.** Close all applications, perform a full shutdown, wait 10 seconds, and restart. Many transient issues causing crashes resolve after a reboot.

2. **Verify the application is not already running in the background.** Open Windows Task Manager (Ctrl+Shift+Esc) and look for the application name in the process list. If it appears multiple times, select each one and click "End Task". Then try launching the application fresh.

3. **Clear the application's temporary cache files.** Most applications store settings and temporary data in a folder. For example, in Windows search, type `%appdata%` and navigate to the application folder (if it exists). Delete any "Temp", "Cache", or "Settings" folders, then restart the application.

4. **Update the application to the latest version.** An older version may have bugs or compatibility issues. Check for updates within the application ("Help" → "Check for Updates") or use the IT Self-Service Portal. If an update is available, install it and try again.

5. **Check for conflicting software.** If you recently installed new antivirus, browser extensions, or system utilities, these can conflict with applications. Temporarily disable them or test the application in Safe Mode (see BSOD section) to isolate the conflict.

6. **Run the application as administrator.** Right-click the application shortcut or executable file and select "Run as administrator". This can resolve permission-related crashes.

7. **Repair the application.** Go to Windows Settings → Apps → Apps and features → find the application → Click on it → "Modify" or "Repair". Follow the on-screen steps to repair corrupted files.

**Escalation:** If the application continues to crash after all steps, uninstall it completely and submit a ticket to [contact IT Helpdesk] with the application name, version, and the error message shown. Include what you were doing when it crashed (opening a specific file, using a feature, etc.).

## Document Signing Tool Not Working or Application Error

**Symptoms:**
- Document signing application fails to launch
- Cannot insert or sign documents
- Error: "Cannot find signing certificate" or "Authentication failed"
- Signed documents are not saving or cannot be opened after signing

**Step-by-step resolution:**

1. **Verify the signing tool is installed correctly.** Go to Windows Settings → Apps → Apps and features and search for the document signing application by name. If it does not appear, reinstall it from the IT Self-Service Portal or ask [contact IT Helpdesk] for the installer.

2. **Check your digital certificate is current and valid.** The signing certificate must not be expired and must be installed on your computer. Go to Windows → Manage user certificates (Windows: search for "certmgr.msc"). Look under "Personal" → "Certificates" for your signing certificate. If it shows "Valid from" date has passed, request a new certificate from [contact IT Helpdesk].

3. **Restart the application and try again.** Close the signing tool completely and reopen it. Many authentication issues resolve with a restart.

4. **Clear the application's cache.** Same process as the Application Crashes section above: open `%appdata%` and delete any Temp or Cache folder specific to the signing application.

5. **Re-authenticate your identity.** Some signing tools require periodic re-authentication. Go to the application settings or "About" menu and select "Re-authenticate", then enter your credentials when prompted.

6. **Test with a simple document.** Try signing a new, simple PDF or document to narrow down the issue. If it works with a new document but not with specific files, the issue may be with that file, not the tool.

7. **Check if your user account permissions are correct.** Some signing tools require specific Windows user permissions. Contact [contact IT Helpdesk] and confirm your account has the necessary permissions to use the signing tool.

**When to escalate:** If you cannot sign documents after all steps, or if you receive an error about your certificate being invalid or expired, submit a ticket to [contact IT Helpdesk] with the error message and details of which documents you are trying to sign. IT can verify your certificate and renew it if necessary.

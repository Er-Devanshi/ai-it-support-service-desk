# Email and Outlook Troubleshooting Guide

## Overview

This guide covers common Outlook and corporate email issues including synchronization failures, missing mail, calendar problems, and account configuration. Follow each section in order before escalating to IT.

---

## Section 1: Email Not Syncing or Loading Slowly

**Symptoms:**
- New email does not appear in the inbox
- The "Send/Receive" progress bar stalls
- Outlook shows "Disconnected" or "Trying to connect…" in the status bar

**Step-by-step resolution:**

1. **Check your internet connection.** Open a browser and confirm other sites load. If there is no internet access, resolve network connectivity first.
2. **Check the Outlook status bar.** Click the "Work Offline" button if it is highlighted — it must be unchecked to allow synchronization.
3. **Force a full send/receive.** Press **F9** or click **Send/Receive → Send/Receive All Folders**.
4. **Restart the Outlook application.** Close all Outlook windows and reopen.
5. **Restart your workstation.** A full reboot clears stale Outlook cache files.
6. **Check mailbox storage quota.** An over-quota mailbox refuses new mail. In Outlook: File → Info → Mailbox Settings → see the mailbox size warning.
7. **Repair the Outlook data file (OST/PST).** In File → Account Settings → Data Files, note the file path, then close Outlook and run `scanpst.exe` on that file. The tool is located in `C:\Program Files\Microsoft Office\root\OfficeXX\`.

**Escalation condition:** If the problem persists after all steps above, or if other users on the same server are affected, escalate to the Collaboration & Email Systems team — this may indicate a server-side or Exchange connector issue.

---

## Section 2: Outlook Authentication Error or Password Prompt Loop

**Symptoms:**
- Outlook repeatedly asks for your username and password
- Error: "Your password has expired" or "Authentication failed"
- Profile disconnects after a few minutes

**Step-by-step resolution:**

1. **Verify your Active Directory password.** Log out of Windows and log back in. If your Windows login succeeds, your AD password is valid.
2. **Clear saved Outlook credentials.** Go to: Control Panel → Credential Manager → Windows Credentials → find entries containing your email domain → remove them → restart Outlook.
3. **Check Modern Authentication (OAuth).** Open Outlook Options → Advanced → uncheck "Use Cached Exchange Mode" temporarily to force a reconnect.
4. **Re-create your Outlook profile.** Control Panel → Mail → Show Profiles → Add new profile with your work email. Use the existing profile only if the new one succeeds.

**Safety note:** Do not share your password with anyone, including IT staff. IT will never ask for your password. If you receive such a request, report it as a phishing attempt.

---

## Section 3: Missing Emails or Accidentally Deleted Messages

**Symptoms:**
- Specific email messages cannot be found
- The Deleted Items folder shows items you did not delete

**Step-by-step resolution:**

1. **Search all folders.** In Outlook, press **Ctrl+Shift+F** → change "Look in:" to "All Folders" → enter subject keywords.
2. **Check Clutter or Focused Inbox.** Microsoft 365 may have auto-sorted messages to these tabs.
3. **Check Junk Email folder.** Legitimate messages occasionally land in Junk.
4. **Recover Deleted Items.** Folder → Recover Deleted Items (Recover items deleted from this folder). This accesses server-side soft-deleted items within the retention window.
5. **Contact IT for litigation hold restore.** If the message is beyond the 30-day soft-delete window, IT can attempt a backup restore if a litigation hold policy is in place.

---

## Section 4: Calendar Synchronization Issues

**Symptoms:**
- Meeting invites do not appear in the calendar
- Delegate access is not updating

**Step-by-step resolution:**

1. Restart Outlook and check Sync Issues folder under the folder list.
2. Verify calendar sharing permissions with the delegate in Outlook → Home → Calendar Permissions.
3. For shared calendars, remove and re-add the calendar: right-click "Shared Calendars" → Add Calendar → From Address Book.

**Escalation condition:** Calendar issues affecting multiple users indicate a server-side Exchange or Microsoft 365 tenant policy issue. Raise a ticket to the Collaboration & Email Systems team.

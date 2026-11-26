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

---

## Section 5: Email Attachment Size Limits and Large File Sharing

**Symptoms:**
- Cannot attach a file larger than 25 MB to an email
- Error: "Attachment exceeds maximum size" or "File is too large to send"
- Need to send large files to colleagues but email attachment is not permitted
- Want to know the exact attachment size limit

**Step-by-step resolution:**

1. **Know the attachment limit.** Most corporate email systems limit individual attachments to 25 MB and total message size to 50 MB. Check your company's email policy in the IT Self-Service Portal or contact [contact IT Helpdesk] for the exact limit for your organization.

2. **For files under the limit:** Compress the file first to reduce size. In Windows: right-click the file → Send to → Compressed (zipped) folder. In macOS: right-click → Compress. This often reduces file size by 30–70%.

3. **For files over the limit, use approved file sharing services:** Upload the file to an approved corporate collaboration tool (such as SharePoint, OneDrive, Teams, or the company's internal file portal). Share the link via email instead of attaching the file directly. This avoids size restrictions and provides version control.

4. **Request a larger attachment exemption (temporary):** If you have a one-time need for a larger attachment, contact IT Support with the business justification. IT can enable a temporary exception or recommend an alternative sharing method.

5. **Split the file into multiple emails:** For large archives, split the content into multiple smaller attachments (each under 25 MB) and send in separate emails. Clearly label them (e.g., "Part 1 of 3").

6. **Check compression options in Outlook:** Outlook can automatically compress images in attachments. Go to File → Options → Mail → Compose messages → and enable "Reduce file size when sending pictures".

7. **Verify the recipient can receive large attachments.** If sending to an external partner, their email system may have a different (usually lower) limit. Ask them what their maximum attachment size is before sending.

**When to escalate:** If you consistently need to send files larger than the corporate limit for your role, or if you believe your attachment limit is set incorrectly, escalate to the Collaboration & Email Systems team. Provide your use case and they can review whether an exemption or policy adjustment is appropriate.

# Software Installation and Access Permissions Guide

## Overview

This guide covers software installation requests, access permission changes, and licence management on corporate devices. All software installations on company-managed equipment must be approved through IT and sourced from authorised channels.

---

## Section 1: Requesting Software Installation

**Important policy notice:**
Do NOT install unlicensed, personal, or unapproved software on company devices. Installing unauthorised software violates the Acceptable Use Policy and may result in disciplinary action.

**Step-by-step process:**

1. **Check the Self-Service Portal first.** Browse to the IT self-service portal (internally linked on the IT SharePoint). Many common applications (Adobe Reader, 7-Zip, Zoom, Teams updates, Chrome, Notepad++) are pre-approved and can be installed without a ticket.
2. **If the application is not listed in the portal:**
   - Submit a software request ticket with:
     - Application name and version
     - Business justification (what work task requires it)
     - Vendor name and licence type (personal, site, subscription)
   - IT will evaluate licensing compliance, security risk, and compatibility.
3. **Do not use administrator privileges to install software yourself.** Managed devices use least-privilege accounts. Attempting to bypass this causes audit alerts.
4. **For annual licence renewals:** Contact IT at least 3 weeks before the expiry date with the current licence key and vendor invoice.

**Typical approval timelines:**
- Pre-approved software: Immediate (via self-service portal)
- New software with standard risk: 2–5 business days
- High-risk or expensive software: up to 10 business days

---

## Section 2: Access Permissions and Role Changes

**Symptoms / Use cases:**
- You need access to a shared drive, SharePoint site, or application
- A team member has left and their access needs to be revoked
- A new hire requires onboarding access

**Step-by-step process:**

1. **Access request (for yourself or new team member):**
   - Submit an access request ticket specifying: the resource name, access level required (read, write, admin), business justification, and approving manager's name.
   - Access to sensitive or restricted systems requires manager approval before IT can grant it.
2. **Access revocation:**
   - For immediate revocation (e.g. employee departure): contact IT by phone or urgent ticket. IT follows the Leaver Procedure checklist which includes disabling the AD account, removing group memberships, and revoking VPN certificates.
3. **Shared mailbox or distribution list changes:**
   - Submit a ticket to Collaboration & Email Systems with the mailbox name and the list of users to add or remove.

**Escalation condition:** If access is time-sensitive (e.g. new hire cannot work), call the IT helpdesk directly rather than waiting for a ticket response.

---

## Section 3: Software Not Launching or Licence Activation Failure

**Symptoms:**
- Application crashes on startup
- "Licence has expired" or "Activate your product" messages appear
- "This application requires administrator rights" error

**Step-by-step resolution:**

1. **Restart the workstation** — most licence validation issues clear after a reboot.
2. **Check date and time.** Licence validation is time-sensitive. Open Date and Time settings and ensure the system clock is synchronised to the corporate NTP server.
3. **Check network connectivity to the licence server.** Some applications validate licences online. If you are working remotely, ensure your VPN is connected.
4. **Repair the application.** Go to Settings → Apps → find the application → Modify or Repair.
5. **Contact IT if the licence key is invalid or expired.** Do not attempt to download or enter licence keys from unofficial sources.

---

## Section 4: Removing or Uninstalling Software

1. Use Settings → Apps → Uninstall, or Programs and Features in Control Panel for legacy applications.
2. If the application does not appear in the list, or if uninstall fails, submit a ticket to IT with the application name. IT uses deployment tools to force removal.
3. Never delete application folders from `Program Files` manually — this leaves behind registry entries that can cause reinstall problems.

# Network Drives and File Access Troubleshooting Guide

## Overview
This guide covers common issues with accessing shared network folders, file shares, and network storage. Follow each section for step-by-step resolution of connectivity and permissions problems.

## Accessing Shared Network Folders

**Symptoms:**
- Cannot see shared network folders on other computers
- Cannot open files stored on shared network drives
- File sharing is unavailable or grayed out
- "Access Denied" error when trying to open shared content

**Step-by-step resolution:**

1. **Verify your computer is connected to the corporate network.** Connect to the office Wi-Fi or wired network, or if working remotely, ensure your VPN is connected and shows "Connected" status. Check your network connection by opening a web browser and verifying you can access websites or company intranet.

2. **Request file share access.** If you are new to your role or trying to access a shared folder for the first time, your IT administrator must grant you permissions. Submit a file share access request through the IT Self-Service Portal or submit a ticket to [contact IT Helpdesk] with the name of the shared folder and your business justification for access.

3. **Access shared folders using the UNC path in Windows.** Open File Explorer, go to the address bar, and type the shared folder path starting with two backslashes (for example, `\\servername\foldername`). Replace servername and foldername with the actual names provided by your team or IT. Press Enter.

4. **On macOS, use "Go" → "Connect to Server".** Open Finder, press Command+K, and enter the network address in the format `smb://servername/foldername`. Click Connect.

5. **Map a network drive for quick access (Windows).** To access a frequently-used shared folder quickly, map it as a drive letter. In File Explorer, right-click "This PC" → "Map network drive", select a drive letter, enter the shared folder path, check "Reconnect at sign-in", and click Finish. The mapped drive appears in your File Explorer sidebar.

6. **Provide your network credentials if prompted.** When connecting to a shared folder for the first time, Windows may ask for your username and password. Enter your corporate domain username (usually in the format "domain\username") and password. Check "Remember my credentials" so you do not need to enter them again.

7. **Check if the shared folder host computer is powered on and connected.** For peer-to-peer file shares (sharing from another employee's computer), that computer must be powered on and connected to the network. If their computer is off or disconnected, the shared folder is unavailable.

**Escalation:** If you receive an "Access Denied" error even though you have submitted an access request, or if the shared folder cannot be located at all, submit a ticket to [contact IT Helpdesk] with the full UNC path and your username. IT will verify your permissions and the folder's availability.

## Files Not Showing in a Shared Drive or Folder

**Symptoms:**
- Shared folder opens but appears empty even though files should be there
- Files that were visible yesterday are now missing
- Partial files are visible but not all expected files
- Recently deleted files are still showing

**Step-by-step resolution:**

1. **Refresh the folder view.** Press F5 in File Explorer to refresh the view. Files may not display immediately if the network connection is slow or if the display cache is stale.

2. **Check folder permissions.** You may have access to the folder itself but not read permissions for specific files. If files are listed but appear grayed out or inaccessible, you may not have permission to read them. Contact the folder owner or [contact IT Helpdesk] to request file-level read access.

3. **Verify you are looking in the correct folder.** Shared drives can have many subfolders. Open "Details" view to see file dates and sizes to confirm you are looking at the right folder. Check the folder path in the File Explorer address bar.

4. **Check for hidden files.** In Windows File Explorer, go to View → Options → Change folder and search options → View tab, and select "Show hidden files, folders, and drives". Click Apply and OK. This reveals files that may be hidden from normal view.

5. **Look for a network delay or sync issue.** If files were recently uploaded, they may not appear immediately due to network or server sync delays. Wait a few minutes and refresh (press F5) again.

6. **Confirm the file has not been moved.** Ask the file owner or use the shared folder's search function (if available) to locate the file in a different subfolder within the share.

7. **Check if the shared folder is a filtered or limited view.** Some shared folders display different content based on user role or department. Verify with your team lead that you have access to the specific files you need.

**Escalation:** If files are confirmed to have been deleted accidentally, submit a ticket to [contact IT Helpdesk] immediately with the file names, folder path, and approximate date they were last accessed. IT may be able to restore files from backup.

## Mapped Network Drive Not Reconnecting or Showing as Unavailable

**Symptoms:**
- Mapped drive shows an "X" or red icon in File Explorer
- "Drive not found" error when trying to access mapped drive
- Mapped drive appears but becomes unavailable after restart or reconnect
- Authentication fails when trying to reconnect

**Step-by-step resolution:**

1. **Restart your computer.** Sometimes mapped drives fail to reconnect after sleep or restart. A full reboot usually restores the connection. Restart and check if the drive reappears and is accessible.

2. **Disconnect and remap the drive.** In File Explorer, right-click the mapped drive and select "Disconnect". Then map it again: right-click "This PC" → "Map network drive", select the same drive letter, re-enter the shared folder path (ask your team if you need the path), check "Reconnect at sign-in", and click Finish.

3. **Verify the host computer or network is accessible.** If the mapped drive points to another employee's computer, ensure their computer is powered on and they are connected to the network. If the mapped drive points to a network server, verify that you are connected to the corporate network or VPN.

4. **Re-enter your network credentials.** Go to Control Panel → Credential Manager → Windows Credentials. Look for entries related to your mapped drive's server or network path. Click on the entry, select "Edit", and re-enter your username and password. This can resolve authentication failures.

5. **Change the mapped drive path if the original is unavailable.** If the original server or share has been moved or renamed, ask your IT administrator for the new path. Disconnect the old mapping and create a new one with the updated path.

6. **Check if VPN is connected (for remote access).** If you mapped the drive while in the office but are now working remotely, your VPN must be connected for the mapped drive to work. Ensure your VPN shows "Connected" status and try accessing the drive again.

**Escalation:** If the mapped drive remains unavailable after all steps, or if you receive persistent authentication errors, submit a ticket to [contact IT Helpdesk] with the mapped drive letter, the network path, and when the issue started. IT can verify the server availability and your credentials.

## Database or Server Access Request

**Symptoms:**
- You need access to a company database, application server, or restricted resource
- You receive "Access Denied" or "Permission Required" errors when trying to connect
- Your team has access but you are new and do not yet have permissions

**Step-by-step process:**

1. **Identify the exact resource and access level needed.** Ask your team lead or the resource owner which database, server, or application you need to access and what access level is required (read-only, read-write, admin, etc.).

2. **Submit an access request through the IT Self-Service Portal or submit a ticket to [contact IT Helpdesk].** Include: the resource name, your username, your manager's name, your business justification (what work task requires this access), and the requested access level.

3. **Provide business justification.** Describe why you need this access and how it relates to your job responsibilities. Example: "I need read access to the customer database to generate monthly reports for my team."

4. **Wait for approval.** Your manager and the resource owner will review and approve the request. This typically takes 1–3 business days. You will receive notification when access is granted.

5. **Once approved, test the connection.** After approval notification, try connecting to the resource using the connection method your IT department provides (hostname, port, connection string, etc.). If access is still denied, contact [contact IT Helpdesk] with the error message.

**Important security notes:**
- Do not share database credentials with other users. Each person must request their own access.
- Do not use production databases for testing. Use the test/development environment if available.
- Do not leave sensitive connections open when you are away from your desk. Close connections and applications when you leave.
- Report suspicious access attempts or unusual errors immediately to IT Security.

**Escalation:** If you are unsure about the resource name or access type, or if you do not receive response to your access request within 3 business days, follow up with [contact IT Helpdesk]. Provide your ticket number if you have one.

# Slow Computer Performance Troubleshooting Guide

## Overview

This guide covers diagnosis and resolution of workstation slowness, high CPU or memory usage, application freezing, and general performance degradation on corporate laptops and desktops.

---

## Section 1: Immediate Steps for a Slow or Unresponsive Computer

**Symptoms:**
- Applications take a long time to open
- Mouse and keyboard input feels sluggish or delayed
- Programs freeze or stop responding
- The system fan runs loudly and continuously
- The battery drains faster than usual (laptops)

**Step-by-step diagnosis and resolution:**

1. **Restart the workstation first.** Many performance issues are caused by memory leaks, stuck processes, or pending Windows updates that install on restart. A full shutdown-and-restart (not just Sleep) clears these.

2. **Check Task Manager for high CPU or memory usage.**
   - Press **Ctrl+Shift+Esc** to open Task Manager.
   - Click the **CPU** column header to sort by CPU usage.
   - If a single process consumes more than 80% CPU continuously, note its name.
   - Common culprits:
     - `MsMpEng.exe` (Windows Defender) — running a scheduled scan. Wait for it to complete.
     - `SearchIndexer.exe` — Windows Search reindexing. Temporary; will finish.
     - `OneDrive.exe` or `Backup client` — syncing large files. Wait or pause sync.
     - Unknown processes with high CPU → **report to IT as a potential malware indicator.**

3. **Check available disk space.**
   - Open File Explorer → right-click Local Disk (C:) → Properties.
   - If free space is below 10%, performance degrades severely.
   - Delete temporary files: press **Win+R** → type `%temp%` → press Enter → select all files → Delete.
   - Run Disk Cleanup: search "Disk Cleanup" in Start → select C: drive → include System Files cleanup.

4. **Check for pending Windows Updates.**
   - Settings → Windows Update → check for and install all available updates.
   - Updates that install in the background during working hours consume CPU and disk I/O.

5. **Close unnecessary applications and browser tabs.**
   - Each open browser tab consumes 50–200 MB of RAM. Close tabs you are not actively using.
   - Close background applications visible in the system tray.

6. **Check memory (RAM) usage.**
   - In Task Manager → Performance tab → Memory.
   - If "In Use" memory consistently exceeds 85% of total, the machine may need a RAM upgrade. Document this and raise a hardware ticket.

---

## Section 2: Slow Startup or Boot Time

**Step-by-step resolution:**

1. **Disable unnecessary startup programs.**
   - Task Manager → Startup tab → right-click and Disable items that are not essential.
   - Common candidates: Spotify, Teams (if not required at login), OneDrive sync clients from personal accounts.
2. **Check for corrupted Windows startup files.**
   - Open Command Prompt as administrator → run: `sfc /scannow`
   - This scans and repairs corrupt system files. Allow it to complete (takes 5–20 minutes).
3. **Check the HDD vs SSD.** Machines with mechanical hard drives are significantly slower than SSDs. If your device boots in more than 3 minutes consistently, IT may be able to upgrade to an SSD. Submit a hardware request ticket.

---

## Section 3: Application-Specific Slowness

**Symptoms:**
- One specific application (e.g. Excel, Outlook, AutoCAD) is slow while others run normally

**Step-by-step resolution:**

1. **Repair the application.** Settings → Apps → find the application → Modify/Repair.
2. **Clear application cache.** For browsers: clear cache and cookies in browser settings. For Outlook: close and delete the `.ost` file to force a resync.
3. **Update the application** to the latest version.
4. **Check if the issue is file-specific.** Open a new blank file in the same application. If the blank file runs quickly, the problem is with a corrupted or oversized data file.

---

## Section 4: Escalation Conditions

Escalate to IT immediately if:
- An unknown process is consuming 80%+ CPU and does not resolve after restart → potential malware.
- Multiple users in the same area report simultaneous slowness → may be a network storage or server issue rather than the individual workstation.
- The workstation has crashed with a Blue Screen of Death (BSOD) — note the error code shown on the blue screen and report it with the timestamp.
- Hardware diagnostics indicate failing storage or overheating.

**When submitting a performance ticket, include:**
- Task Manager screenshot or list of high-CPU processes
- Available disk space percentage
- Approximate time the slowness started
- Whether a recent software installation or update preceded the issue

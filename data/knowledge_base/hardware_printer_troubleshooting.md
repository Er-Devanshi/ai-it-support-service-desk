# Enterprise Hardware and Printer Troubleshooting Standard

## Common Network Printer Diagnostics
Network printers are connected to departmental print servers (`print-srv01.corp.internal`).

### Stuck Print Queue
When print jobs queue indefinitely with status "Printing" or "Error":
1. Check physical printer status: ensure paper trays are loaded, toner is sufficient, and no paper jams exist.
2. Open Windows Services (`services.msc`) and locate the **Print Spooler** service.
3. Stop the Print Spooler service.
4. Navigate to `C:\Windows\System32\spool\PRINTERS` and delete any pending `.spl` or `.shd` spool files.
5. Restart the Print Spooler service.
6. Submit a 1-page test document to verify queue clearance.

### Departmental Printer Offline
If the printer shows as "Offline" in Windows Settings:
1. Ping the printer's static IP address from the command prompt: `ping 10.20.4.50`.
2. If unreachable, inspect the Ethernet cable connected to the wall port and check link lights on the switch.
3. Power-cycle the printer: turn off the main switch, wait 30 seconds, and power on.
4. Verify DHCP or DNS lease on the print server.

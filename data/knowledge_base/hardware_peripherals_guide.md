# Hardware and Peripherals Troubleshooting Guide

## Overview
This guide covers common hardware device issues including peripherals (keyboard, mouse, monitor), power problems, and system crashes. Follow each section for step-by-step troubleshooting.

## Keyboard or Mouse Not Working

**Symptoms:**
- Keyboard or mouse does not respond to input
- Keys press but nothing happens on screen
- Cursor does not move or mouse clicks are not recognized
- Device was working but stopped abruptly

**Step-by-step resolution:**

1. **Check physical connections (wired devices).** For USB keyboards or mice, ensure the cable is firmly connected to a USB port on your computer. Try a different USB port if available.

2. **Replace batteries (wireless devices).** For wireless keyboards or mice, replace the batteries with fresh ones. Try alkaline batteries for best results. Verify the device powers on (look for LED indicator).

3. **Restart your computer.** Power off completely, wait 10 seconds, and power back on. Many device driver issues clear after a reboot.

4. **Re-establish the wireless connection (wireless devices).** For Bluetooth or radio-frequency wireless devices, re-pair or reconnect: Look for a "Connect" or "Pair" button on the device. Hold it for 3–5 seconds while the receiver/adapter is plugged in. The device should reconnect automatically.

5. **Check Device Manager for errors (Windows).** Press Windows key + X, select Device Manager, and expand "Keyboards" and "Mice and other pointing devices". If any device shows a yellow exclamation mark, right-click it and select "Update driver". If that fails, uninstall and restart your computer to reinstall automatically.

6. **Test with an external keyboard or mouse.** Borrow a known-good USB keyboard or mouse and plug it into your computer. If the external device works, your original device may be faulty.

7. **Disable and re-enable the device.** In Device Manager (see step 5), right-click your device and select "Disable device". Wait 5 seconds, then right-click again and select "Enable device".

**Escalation:** If an external keyboard or mouse works but your original device does not, the original device is likely faulty. Submit a ticket to [contact IT Helpdesk] with your device serial number for replacement.

## Monitor or Display Showing Strange Colors or Not Displaying Correctly

**Symptoms:**
- Monitor displays colors that do not match screen content (purple tint, green hue, etc.)
- Display is flickering or flashing
- Monitor shows "No Signal" or remains black
- Partial display or image is cut off on the edges
- Text or images appear distorted

**Step-by-step resolution:**

1. **Check monitor power and cable connections.** Ensure the power cable is securely connected and the monitor is powered on (look for a power indicator light). Check that the video cable (HDMI, DisplayPort, or VGA) is firmly seated at both the monitor and computer.

2. **Try a different video cable.** If available, borrow a spare video cable and test with it. Some cables can degrade over time or have internal damage causing signal issues.

3. **Power cycle the monitor.** Turn the monitor off, wait 10 seconds, and turn it back on. This can reset the display and clear temporary glitches.

4. **Adjust monitor settings.** On the monitor itself (using physical buttons on the side or bottom), look for a "Menu" or "Settings" button. Find "Color" or "Picture Settings" and reset to defaults. Check the brightness and contrast sliders to ensure they are not at extreme values.

5. **Check cable connection at the graphics card (Windows).** Power off your computer. On the back of the CPU tower, locate the monitor cable connection (not onboard USB or Ethernet). Reseat the cable by unplugging and firmly replugging it. Power back on.

6. **Test with a different monitor.** If possible, borrow another monitor and connect it to your computer with the same cable. If the borrowed monitor displays correctly, your original monitor may be faulty.

7. **Update graphics card drivers.** Press Windows key + X, select Device Manager, expand "Display adapters", right-click your graphics card (usually "Intel", "NVIDIA", or "AMD"), and select "Update driver". Restart if prompted.

**Escalation:** If a different monitor displays correctly or if the issue persists after all steps, submit a ticket to [contact IT Helpdesk] with your monitor model and graphics card details. The hardware may need replacement.

## Computer Won't Power On or Won't Start

**Symptoms:**
- Press the power button but nothing happens
- No lights, fans, or beeping sounds
- Computer powers on briefly then shuts down
- Stuck on manufacturer logo or black screen

**Step-by-step resolution:**

1. **Check power cable and outlet.** Ensure the power cable is firmly connected to both the computer and the power outlet. Test the outlet by plugging in a different device (such as a desk lamp) to verify the outlet is working.

2. **Look for power indicator lights.** Most computers have LED indicators near the power button. If no lights are on, the power supply may not be working.

3. **Listen for beeping or fan sounds.** If you hear fans or beeping when you press power, internal power is working but the display may not be connected. See the Monitor section above.

4. **Press and hold the power button for 15 seconds.** This performs a hard shutdown and can clear stuck processes. Release, wait 5 seconds, and press again to power on normally.

5. **Leave the computer off for 2 minutes, then try again.** This can help if the system got into a failed startup loop. Wait at least 2 minutes before restarting.

6. **Check for external connections that might interfere.** Unplug all USB peripherals except keyboard and mouse. Remove any external drives or docking stations. Power on again.

7. **If the computer powers on but gets stuck on startup.** You may see a "Windows is Starting Up" message or manufacturer logo that does not progress. This may indicate a software issue. Wait 5 minutes (some updates take time), and if still stuck, perform a hard shutdown (hold power button 15 seconds) and try again.

**Escalation:** If none of the above steps work, the computer may have a hardware failure (power supply, motherboard, or other component). Submit a ticket to [contact IT Helpdesk] with the serial number and a description of what you observe (power lights, sounds, error messages). Request an in-person diagnosis or hardware replacement.

## Blue Screen or System Crash

**Symptoms:**
- Computer suddenly displays a blue screen with error text and stops responding
- Error message includes "DRIVER IRQL NOT LESS OR EQUAL", "SYSTEM SERVICE EXCEPTION", or similar
- Computer restarts unexpectedly without warning
- Application freezes and you see "Not Responding" in the title bar

**Common causes:**
- Driver software issue (usually a recently installed or updated driver)
- Hardware malfunction (faulty RAM, hard drive, or other component)
- Malware or antivirus conflict
- System overheating (computer runs very hot or loud)

**Step-by-step response:**

1. **Write down or photograph the error message.** If you see a blue screen, take a photo of the entire message, including any error code (like "0x0000007E") or file name mentioned.

2. **Perform a hard shutdown and try again.** Hold the power button for 15 seconds to force shutdown, wait 5 seconds, then power on normally. The system may start up without crashing the second time.

3. **Check if a recent driver or software installation preceded the crashes.** If you installed new software, updated drivers, or installed a Windows update just before the crashes started, this could be the cause. Restart your computer in Safe Mode: Restart → Hold Shift and click Power Off → Power On → Select "Troubleshoot" → "Advanced options" → "Startup Settings" → Restart and choose "Safe Mode". If the computer is stable in Safe Mode, uninstall the recent software or update and try again in normal mode.

4. **Verify the computer is not overheating.** Check if the fans are running loudly or if the computer feels very hot. Dust can block air vents. Use compressed air to gently blow dust out of vents (CPU tower, monitor, power supply). Ensure the computer is on a hard surface with air flow around it, not on a soft surface like a bed.

5. **Run an antivirus scan.** Boot into Safe Mode (see step 3) and run a full system scan with your antivirus software. Malware can cause system crashes.

**When to escalate:** If crashes continue even in Safe Mode, or if you see the same error code multiple times, escalate to [contact IT Helpdesk] with the error message and details of when the crashes occur (always during a specific application, randomly, etc.). Provide the photos of error screens if available.

## Webcam or Microphone Not Detected

**Symptoms:**
- Video calls freeze or show no image from your camera
- No audio input or microphone is not picking up sound
- Application says "No camera found" or "No microphone detected"
- Device manager does not show camera or microphone

**Step-by-step resolution:**

1. **Check physical connections.** For USB webcams or microphones, ensure the cable is firmly connected to a USB port. Try a different USB port.

2. **Verify the device is powered on.** For external cameras and microphones, check for power lights or battery indicators. Replace batteries if needed.

3. **Check application permissions (Windows 10/11).** Go to Settings → Privacy & Security → Camera (or Microphone). Ensure the toggle for your application is turned ON. Some applications need to be restarted after permission is granted.

4. **Restart your computer.** Sometimes drivers initialize correctly only after a full restart.

5. **Check Device Manager for the device.** Press Windows key + X, select Device Manager, and look under "Imaging devices" (camera) or "Audio inputs and outputs" (microphone). If the device appears with a yellow exclamation mark, right-click it and select "Update driver". Restart if prompted.

6. **Disable and re-enable the device.** In Device Manager, right-click the camera or microphone, select "Disable device", wait 5 seconds, right-click again and select "Enable device".

7. **Test with another application.** Try using the camera or microphone in a different application (like Windows Camera app or Sound Recorder). This tells you if the device is detected by Windows or if it's an application-specific issue.

8. **Uninstall and reinstall the driver.** In Device Manager, right-click the device and select "Uninstall device" (check "Delete the driver software" if available). Restart your computer. Windows should automatically reinstall the driver.

**Escalation:** If the device appears in Device Manager but applications still cannot access it, or if Device Manager does not show the device at all, submit a ticket to [contact IT Helpdesk] with your device model and operating system. The device may require specific drivers or may be faulty.

# CourtVision 🎾 — Operator Troubleshooting Guide

This guide provides simple step-by-step instructions for resolving operational issues during setup or live execution.

---

## 🛠 Troubleshooting Matrix

| Problem | Likely Cause | Solution |
| :--- | :--- | :--- |
| **Camera Preview Blank / Black** | USB disconnected or wrong source selected | 1. Check USB cable.<br>2. Select correct camera source from dropdown.<br>3. Click **▶ START CAMERA**. |
| **Virtual Ad Floats / Shifted** | Camera moved after calibration | Click **⚙ CALIBRATE COURT** and re-select the 4 baseline corners. |
| **Advertisement Not Showing** | Ad disabled or image missing | 1. Open **📢 ADS MANAGER**.<br>2. Confirm checkbox is checked.<br>3. Confirm graphic PNG file exists in `ads/`. |
| **Video Preview Stuttering / Lag** | High system load | Select **Quality: Performance** (320px) from toolbar. |
| **RTSP Stream Disconnected** | Network cable unplugged or IP change | CourtVision automatically attempts reconnects. Check network Ethernet cable. |
| **Recording Fails to Start** | Destination drive full | Ensure disk has free space and `output/` folder is writable. |

---

## 🔁 Quick System Recovery

If the application ever stops responding:
1. Click **⏹ STOP RECORDING** (if recording was active).
2. Close CourtVision cleanly.
3. Relaunch **CourtVision**. Session restoration will reload your court calibration and active profile automatically.

# CourtVision 🎾 — Installation & Desktop Setup Guide

This guide describes how to install, test, update, and uninstall CourtVision on a production Windows PC.

---

## 🖥 System Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **RAM**: 8 GB minimum (16 GB recommended)
- **Disk Space**: 2 GB free space
- **Camera Input**: USB Webcam (1080p @ 30 FPS) or RTSP IP Camera
- **Software Dependencies**: NONE. Python, PyTorch, and OpenCV are pre-bundled into the executable.

---

## 📥 Installation Steps

### Option A: Standard Setup Installer (`CourtVision-Setup.exe`)
1. Download or copy `CourtVision-Setup.exe` to your computer.
2. Double-click `CourtVision-Setup.exe`.
3. Select your installation folder (Default: `C:\Program Files\CourtVision`).
4. Keep **Create a Desktop Shortcut** checked.
5. Click **Install**, then click **Finish**.

### Option B: Standalone Portable Folder (`release/CourtVision/`)
1. Copy the `CourtVision` folder to your computer's `Desktop` or `C:\CourtVision`.
2. Double-click `CourtVision.exe` to launch directly without running an installer.

---

## 🔄 First Launch & Verification

1. Double-click the **CourtVision** desktop icon.
2. The application window will launch in Dark Control Room operator mode.
3. Verify the window header shows `CourtVision Desktop Control Center v1.0.0`.
4. Ensure no pop-up error messages appear.

---

## 🗑 Uninstallation Procedure

To remove CourtVision cleanly:
1. Open Windows **Settings** > **Apps** > **Installed apps**.
2. Search for **CourtVision**.
3. Click **Uninstall** and follow the prompts.
4. User court profiles (`config/`) and recorded videos (`output/`) are preserved in your user directory so your court calibrations are never accidentally deleted during an update.

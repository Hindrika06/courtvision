# CourtVision 🎾 — Operator Quick Start Guide

This guide enables an operator to take a standard Windows laptop or PC and deploy CourtVision from installation to match recording in under 10 minutes.

---

## ⚡ 10-Step Rapid Operator Workflow

```text
Fresh Windows PC
      ↓
1. Install CourtVision (Run CourtVision-Setup.exe)
      ↓
2. Mount & Connect Camera (USB Webcam or RTSP Stream)
      ↓
3. Launch CourtVision Desktop Control Center
      ↓
4. Select Active Court Profile (e.g., Court 1)
      ↓
5. Perform 4-Point Court Corner Calibration
      ↓
6. Load Sponsor Advertisements & Set Opacity
      ↓
7. Start Live Camera Processing Preview
      ↓
8. Start Video Recording ([ RECORD VIDEO ])
      ↓
9. Monitor Match & Perform Live Ad Switch
      ↓
10. Stop Recording & Safely Exit
```

---

## 🚀 Detailed Step-by-Step Instructions

### Step 1: Install CourtVision
1. Double-click `CourtVision-Setup.exe` on your desktop or flash drive.
2. Follow the setup wizard prompts and click **Finish**.
3. Launch **CourtVision** from the Desktop shortcut or Start Menu.

### Step 2: Connect Camera
1. Plug your stationary camera USB cable into your computer (or ensure your RTSP IP camera network cable is connected).
2. Ensure the camera tripod is firmly locked and focused on the tennis/badminton court.

### Step 3: Launch & Select Court Profile
1. In the top toolbar of CourtVision, click the **Court Profile** dropdown.
2. Select your court (e.g. `Court 1` or `Court 2`).

### Step 4: Calibrate Court Corners
1. Click **⚙ CALIBRATE COURT**.
2. Click the 4 corners of the court baseline in order:
   - Point 1: **Far-Left Corner**
   - Point 2: **Far-Right Corner**
   - Point 3: **Near-Right Corner**
   - Point 4: **Near-Left Corner**
3. Click **SAVE & APPLY**. The sponsor graphics will instantly snap to the court floor surface.

### Step 5: Configure Advertisements
1. Click **📢 ADS MANAGER**.
2. Select your sponsor graphics (e.g. `ad1.png`, `ad2.png`).
3. Set desired opacity (Recommended: `0.85` for realistic floor sticker texture).
4. Click **ENABLE AD**.

### Step 6: Start Live Processing
1. Click **▶ START CAMERA**.
2. Verify that players walk naturally over virtual advertisements without being obscured or blurred.

### Step 7: Start Match Recording
1. Click **🔴 RECORD VIDEO**.
2. Verify that the recording status indicator turns green and displays active duration.

### Step 8: Live Ad Switching During Gameplay
1. During match timeouts or game changes, click **📢 ADS MANAGER**.
2. Toggle active ads or change opacity. The live stream will switch graphics seamlessly without stopping the camera or recording.

### Step 9: Stop Recording & Verify Output
1. When the match ends, click **⏹ STOP RECORDING**.
2. Open the `output/` folder to view your timestamped MP4 recording (e.g., `session_2026-10-07_193000.mp4`).

### Step 10: Safe Shutdown
1. Click **❌ EXIT** or close the window. CourtVision automatically saves all court profile settings, calibration matrices, and session preferences.

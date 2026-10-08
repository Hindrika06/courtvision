# CourtVision 🎾 — Safe Shutdown Procedure

This guide details the procedure for stopping match recordings and safely exiting CourtVision to guarantee data integrity.

---

## 🛑 Safe Shutdown Workflow

1. **Stop Match Recording**:
   Click **⏹ STOP RECORDING** in the top control toolbar. Wait for the status indicator to change from green ("RECORDING ACTIVE") to neutral ("READY").

2. **Verify Recorded File**:
   Open the `output/` folder and ensure the newly recorded match MP4 file is listed (e.g. `session_2026-10-07_193000.mp4`).

3. **Stop Camera Processing**:
   Click **⏹ STOP CAMERA** to close the video capture device cleanly.

4. **Exit Application**:
   Click the window close button (**❌**) or select **File > Exit**. CourtVision automatically writes active settings to `config/session.json` so your calibration and court preferences load automatically on next launch.

---

## 🔒 Backup & Recovery Recommendation

Before leaving the venue, operators can create a backup copy of calibration profiles and sponsor assets:

```text
Create folder: CourtVision-Backup/
Copy:
├── config/
└── ads/
```

This guarantees your court calibrations can be restored instantly if the operating laptop is swapped.

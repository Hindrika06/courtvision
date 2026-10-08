# CourtVision 🎾 — Field Validation Checklist (Phase 28)

Use this checklist during real-world court testing and staging deployments.

---

## 1. Clean Machine Windows Validation
- [ ] Install/extract application on Windows 10/11 machine without Python/PyTorch/OpenCV/CUDA installed.
- [ ] Launch `CourtVision.exe` directly from Windows Explorer.
- [ ] Confirm app opens without prompt for Python, pip, or virtual environment.
- [ ] Verify zero console/terminal windows appear during normal operator usage.
- [ ] Confirm AI model `models/yolov8n-seg.pt` is detected and loaded.
- [ ] Confirm `config/`, `ads/`, `output/`, and `logs/` folders initialize in user data area.
- [ ] Verify clean application shutdown without zombie processes.

---

## 2. Installer & Uninstaller Validation
- [ ] Run `CourtVision-Setup.exe` installer executable.
- [ ] Verify installation completes to default path (e.g. `C:\Program Files\CourtVision`).
- [ ] Verify Start Menu and Desktop shortcuts are created.
- [ ] Launch via shortcut and confirm full GUI functionality.
- [ ] Uninstall CourtVision via Windows Control Panel / Settings.
- [ ] Confirm application binaries are removed.
- [ ] Confirm user configuration (`config/`), ads (`ads/`), and recordings (`output/`) are preserved in user data directory (`%LOCALAPPDATA%\CourtVision`).

---

## 3. Physical Camera Validation
- [ ] Connect physical USB camera (1080p @ 30 FPS).
- [ ] Select camera source in Desktop UI (`Webcam 0`).
- [ ] Verify live preview initializes within 2 seconds without frame freezing.
- [ ] Measure input acquisition FPS, processing FPS, and total frame latency.

---

## 4. Real RTSP Camera Stream Validation
- [ ] Configure RTSP URL (e.g. `rtsp://192.168.1.100:554/stream1`).
- [ ] Verify stream opens and live video preview updates smoothly.
- [ ] Confirm RTSP passwords/credentials are masked in logs and UI (`sanitize_url`).
- [ ] Perform temporary network disconnect test (unplug network cable for 10 seconds).
- [ ] Verify status updates to `● RECONNECTING...`.
- [ ] Reconnect network cable and verify auto-reconnect restores live stream automatically.

---

## 5. Real Court 4-Point Homography Calibration
- [ ] Launch interactive Calibration Wizard (`⚙ CALIBRATE COURT`).
- [ ] Click far-left, far-right, near-right, near-left court corners accurately.
- [ ] Save calibration and verify points write to active profile's `court.json`.
- [ ] Verify virtual ad overlay aligns perfectly with real court baselines.
- [ ] Confirm ads stay fixed to the playing surface with zero drift under static camera conditions.

---

## 6. Player Occlusion Protection
- [ ] **Stationary**: Player stands on virtual ad $\rightarrow$ player pixels 100% original, no ad painted on player.
- [ ] **Walking**: Player walks across baseline ad $\rightarrow$ player body/feet remain sharp with no ad bleed.
- [ ] **Running**: Player runs fast across court $\rightarrow$ IoU tracker maintains player protection mask continuously.
- [ ] **Fast Movement**: Rapid lateral court movement $\rightarrow$ zero player transparency or bounding box artifacts.
- [ ] **Lunging**: Deep court lunge $\rightarrow$ extended limbs remain fully protected.
- [ ] **Multi-Player**: Two players cross court ads simultaneously $\rightarrow$ both players protected independently.
- [ ] **Enter/Exit**: Player enters/leaves ad boundary $\rightarrow$ smooth mask transitions without ghosting.

---

## 7. Fine Object & Racket Protection
- [ ] **Racket Beside Player**: Racket held next to torso $\rightarrow$ racket head and shaft remain original pixels.
- [ ] **Racket Extended**: Racket extended away from body over ad $\rightarrow$ fine object detector mask covers racket.
- [ ] **Fast Forehand / Backhand**: Rapid swing over baseline ad $\rightarrow$ racket rim protected.
- [ ] **Overhead Shot**: Racket raised high over court baseline $\rightarrow$ racket head protected.
- [ ] **Thin Strings**: Observe string segmentation at medium/far distance $\rightarrow$ document resolution limitation if strings are sub-pixel.

---

## 8. Surface Lighting & Exposure Adaptation
- [ ] Test under bright indoor stadium lighting.
- [ ] Test under normal indoor club lighting.
- [ ] Test under low lighting / uneven shadows across court.
- [ ] Verify surface lighting adaptation adjusts ad brightness naturally without temporal flickering or pop-in.

---

## 9. Temporal Stability
- [ ] Process 10-minute continuous gameplay stream.
- [ ] Verify zero ad jumping, drifting, or perspective warping jitter.
- [ ] Verify protection masks remain temporally stable frame-to-frame.

---

## 10. Live Advertisement Switching
- [ ] Operator changes active ad in Advertisement Manager (`ads.json`).
- [ ] Apply changes live during continuous video processing.
- [ ] Verify new ad renders immediately without stopping the camera or reloading YOLO models.
- [ ] Toggle per-ad opacity slider (0.0 to 1.0) and verify real-time blending update.

---

## 11. Multi-Court Profile Switching
- [ ] Select `Court 1` $\rightarrow$ verify `Court 1` calibration and ads load.
- [ ] Select `Court 2` $\rightarrow$ verify stream releases cleanly, `Court 2` calibration/ads load.
- [ ] Modify `Court 2` ads $\rightarrow$ switch back to `Court 1` and verify `Court 1` configuration is 100% isolated and unchanged.
- [ ] Restart application $\rightarrow$ confirm active court profile is restored from `config/session.json`.

---

## 12. Timestamped Broadcast Recording
- [ ] Start recording via GUI (`⏺ RECORD VIDEO`).
- [ ] Record continuous 5-minute session $\rightarrow$ verify file saved to `output/session_YYYY-MM-DD_HHMMSS.mp4`.
- [ ] Record continuous 15-minute session $\rightarrow$ verify file integrity and playability in standard media player.
- [ ] Record continuous 30-minute session $\rightarrow$ verify file size and video/audio sync.

---

## 13. Long-Run Stability & Resource Monitoring
- [ ] Run live processing loop for 30–60 minutes continuously.
- [ ] Record initial RAM, peak RAM, and final RAM (verify < 10 MB RAM variance, no memory leaks).
- [ ] Record initial CPU %, average CPU %, and peak CPU %.
- [ ] Verify zero dropped frame counter runaway or worker thread deadlocks.

---

## 14. Camera Disconnect / Reconnect Handling
- [ ] Disconnect physical camera or RTSP stream during active processing loop.
- [ ] Verify app transitions state gracefully without GUI freeze or crash.
- [ ] Reconnect camera $\抓$ verify stream resumes processing automatically.

---

## 15. Crash Trapping & Production Logging
- [ ] Inspect `logs/courtvision.log` for sanitized entry formatting.
- [ ] Simulate non-critical configuration error $\rightarrow$ verify operator popup appears with log file reference.

---

## 16. FPS & Real-World Benchmarking
- [ ] Measure `Production Mode` (640x640): Record average FPS, min FPS, max FPS.
- [ ] Measure `Performance Mode` (320x320): Record average FPS, min FPS, max FPS.

---

## 17. System Thermal & Hardware Stability
- [ ] Monitor CPU/GPU temperatures during 30-minute continuous run (if hardware sensors available).
- [ ] Verify no thermal throttling degradation occurs.

---

## 18. Visual Acceptance Final Verification
- [ ] Ad perspective correct and flat on court surface.
- [ ] Player pixels 100% sharp and original (no blur/transparency/bounding box).
- [ ] Racket head protected during play.
- [ ] Stream Health HUD reporting clean metrics.

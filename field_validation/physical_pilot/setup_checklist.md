# CourtVision 🎾 — Physical Setup Checklist (Phase 29)

Use this setup log to record physical camera mounting, court geometry, lighting, and computer hardware metadata prior to launching the pilot.

---

## 📷 1. Camera & Hardware Setup Record

```text
Pilot Date: YYYY-MM-DD
Court Location: Indoor Stadium / Court 1
Court Type: Badminton / Tennis
Camera Manufacturer: Logitech / Dahua / Hikvision
Camera Model: Brio 4K / NVR RTSP Camera
Camera Type: USB / RTSP Stream
Connection URL: rtsp://<sanitized-address>/stream1
Target Resolution: 1920x1080
Target Frame Rate: 30 FPS
Lens / FOV: 90° Wide Angle
Camera Mount Height: 3.5 metres above baseline
Camera Distance: 8.0 metres behind baseline
Computer Model: Production Laptop / Workstation
CPU: Intel Core i7 / AMD Ryzen 7
GPU: Integrated Graphics / Dedicated GPU
RAM: 16 GB DDR4
Windows Version: Windows 11 Pro 64-bit
CourtVision Version: CourtVision v1.0.0
```

---

## 📐 2. Physical Camera Mounting Guidelines

- [ ] **Stationary Mount**: Camera securely mounted on heavy tripod or wall rig; zero physical movement or vibration during play.
- [ ] **Elevation**: Mount camera at an elevated height (3.0m – 4.5m) behind the court baseline for optimal perspective angles.
- [ ] **Framing**: Ensure all four court corners (far-left, far-right, near-right, near-left) and baseline ads are fully visible in the frame.
- [ ] **Lighting Alignment**: Avoid direct sun glare or high-intensity spotlights pointing directly into the camera lens.
- [ ] **Cable Security**: Secure USB or Ethernet cables to prevent accidental unplugging during live match recording.

---

## 💻 3. Production Computer Verification

- [ ] Verify standalone package `release/CourtVision/CourtVision.exe` runs without requiring Python environment installation.
- [ ] Confirm no terminal console windows pop up in operator mode.
- [ ] Confirm AI model `models/yolov8n-seg.pt` is present and verified on startup.
- [ ] Confirm user data folders (`config/`, `ads/`, `output/`, `logs/`) are writable in user data area.
- [ ] Verify display scaling is set to 100% / 125% for Tkinter GUI.

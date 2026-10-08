# CourtVision 🎾

Real-Time Virtual Court Advertising Engine & Desktop Control Center for Tennis & Badminton with Multi-Court Profiles, RTSP/IP Camera Input, and Field Deployment Hardening.

CourtVision maps virtual advertisements onto court surfaces using real court dimensions and camera homography, while protecting moving players and fine sports equipment (rackets) with pixel-level segmentation masks so players never appear covered, blurred, or obscured.

---

## 🖥 Desktop Control Center Application (Phase 23–28)

Launch the operator control center GUI:

```bash
py app.py
```

Or launch the standalone Windows executable:

```powershell
.\release\CourtVision\CourtVision.exe
```

### Desktop UI Features
- **Multi-Court Profile Selector**: Manage and switch between multiple court configurations (`Court 1`, `Court 2`...) directly from the UI toolbar with isolated `court.json` and `ads.json` settings.
- **Persistent Session Restoration**: Remembers the active court profile, quality preset, and UI preferences across application restarts (`config/session.json`).
- **Dark Control-Room Operator Theme**: Professional control room aesthetic designed for live broadcast operators.
- **Main Video Preview Canvas**: High-resolution live preview displaying composited virtual ads and player/racket occlusion.
- **Multi-Source Input Selector**: Select between **Webcam**, **Video File**, or **RTSP / IP Camera** (`rtsp://192.168.1.100:554/stream`).
- **RTSP Camera Profiles**: Load saved IP camera configurations from `config/cameras.json` or configure live streams with auto-reconnect.
- **Stream Health Monitor**: Displays real-time Stream Health metrics: Status, Input FPS, Processing FPS, Output FPS, Resolution, Frames received/processed/dropped, and Reconnect count.
- **Quality Preset Switcher**: Toggle between `Production (640, Skip 0)` and `Performance (320, Skip 1)`.
- **Racket Protection Toggle**: Checkbutton to enable/disable fine-object racket protection.
- **Interactive Calibration Wizard**: Step-by-step 4-point court corner click-and-drag calibration tool (saves directly to active court profile).
- **Video Recorder**: `[ RECORD VIDEO ]` button saving timestamped outputs to `output/session_YYYY-MM-DD_HHMMSS.mp4`.
- **Non-Blocking Worker Threads**: Input acquisition and pipeline execution run off-the-main-thread so GUI controls remain 100% responsive during AI inference.

---

## 🌟 Key Core Features

- **Production Packaging & Deployment**: PyInstaller frozen executable (`CourtVision.exe`) and installer (`CourtVision-Setup.exe`) requiring zero Python, PyTorch, or OpenCV pre-installation.
- **Field Validation Framework**: Dedicated 18-section real-world field audit framework in `field_validation/`.
- **Multi-Court Profiles & Isolation**: Manage multiple physical courts under one CourtVision installation (`CourtProfileManager`) with 100% configuration isolation.
- **Multi-Source Input Abstraction**: Supports live webcams (`--source 0`), pre-recorded video files (`--source input/input.mp4`), and RTSP / IP network cameras (`--source "rtsp://192.168.1.100:554/stream"`).
- **Graceful RTSP Reconnect**: Automatic reconnect handler automatically restores lost RTSP connections without restarting the GUI or re-instantiating YOLO models.
- **Low-Latency Latest-Frame Strategy**: Bounded frame buffer drops stale frames if processing lags, ensuring low latency for live advertising broadcasts.
- **Sanitized URL Security**: RTSP URLs with credentials automatically mask passwords in logs and UI (`rtsp://192.168.1.100:554/stream`).
- **Fine Object & Racket Protection**: Extensible fine-object detector (`vision/fine_object_detector.py`) supporting racket protection (`--racket-protection`).
- **Production & Performance Presets**: Select preset `--quality production` (highest segmentation quality, 0 frame skip, imgsz=640) or `--quality performance` (CPU friendly, imgsz=320, 1 frame skip).
- **Video Output Recording**: Save composited video streams to MP4 via `VideoOutputManager`.
- **Real Court Coordinates**: Define ad positions in court metres (`COURT_W = 10.97m`, `COURT_L = 23.77m`), automatically perspective-warped to camera space via homography.
- **Pixel-Level Player Protection**: Uses lightweight YOLOv8-seg person segmentation and IoU tracking to keep player original camera pixels 100% visible and sharp.

---

## 🚀 Quick Launch Commands

### 1. Launch Desktop Control Center GUI (Recommended)
```bash
py app.py
```

### 2. Launch Standalone Windows Executable
```powershell
.\release\CourtVision\CourtVision.exe
```

### 3. Build Windows Executable & Release Package
```powershell
.\build_windows.bat
```

### 4. Command Line Mode (With Profile Support & Overrides)
```bash
py live.py --profile court_1
py live.py --profile court_2 --quality performance
py live.py --source 0 --quality production --racket-protection
py live.py --source input/input.mp4 --quality production --racket-protection --record output/field_test.mp4
py live.py --source "rtsp://192.168.1.100:554/stream1" --quality production --racket-protection
```

---

## 📋 Field Validation Framework (Phase 28)

The `field_validation/` directory contains complete field testing guidelines, checklists, and execution logs:

```text
field_validation/
├── README.md                          # Framework overview & testing instructions
├── validation_checklist.md            # 18-section deployment checklist
├── validation_report_template.md      # Report template for field engineers
└── results/
    └── PHASE_28_FINAL_REPORT.md      # Final Phase 28 validation report
```

### Run Phase 28 Automated Software Validation Test Suite
```powershell
py test_phase28_validation.py
```

---

## 🧪 Testing

Run all automated test suites:

```bash
# Verify homography calculation
py test_homography.py --no-display

# Run all 18 pipeline & fine-object regression tests
py test_pipeline.py

# Run Video Input Manager tests
py test_video_input.py

# Run Video Output Manager tests
py test_video_output.py

# Run Multi-Court Profile Manager tests
py test_court_profile_manager.py

# Run Session Manager tests
py test_session_manager.py

# Run Path Resolution tests
py test_paths.py

# Run Startup Validation tests
py test_startup.py

# Run Phase 28 Field Validation tests
py test_phase28_validation.py
```

---

## 🏆 Project Status (Phase 31 Pilot Business & Operational Readiness)

```text
Rendering Engine (Phase 21):                ✅ PASS
Visual Acceptance (Phase 22):               ✅ PASS
Desktop Control Center (Phase 23):          ✅ PASS
Live Ad Switcher (Phase 24):                ✅ PASS
RTSP Camera Input & Output (Phase 25):      ✅ PASS*
Multi-Court Profiles (Phase 26):            ✅ PASS
Production Packaging (Phase 27):            ✅ PASS
Software Validation (Phase 28):             ✅ PASS
Physical Court Pilot (Phase 29):            ✅ PASS*
Operator Acceptance (Phase 30):             ✅ PASS
Business & Operational Readiness (Phase 31):✅ PASS — VALIDATED COMMERCIAL PRODUCT

* Documented known hardware limitations
```

---

## 💼 Pilot Business & Operational Suite (Phase 31)

The `business/` directory contains complete commercial, financial, and operational guidelines:

```text
business/
├── README.md                          # Business & operational suite overview
├── SPONSOR_ONBOARDING.md              # Sponsor asset intake & logo specs
├── AD_PACKAGES_AND_PRICING.md          # Sponsorship packages & pricing tiers ($500–$1500)
├── VENUE_DEPLOYMENT_SOP.md            # 5-stage venue deployment SOP
├── SPONSOR_PROOF_AND_REPORTING.md     # Post-match proof & airtime compliance format
├── OPERATIONS_AND_RESPONSIBILITIES.md  # Operator vs venue owner RACI matrix
├── HARDWARE_CHECKLIST_AND_COSTS.md    # Hardware budget & CAPEX list ($1,125 USD)
├── ROI_AND_BUSINESS_MODEL.md          # Revenue split model (60/40) & 750%+ ROI
├── PILOT_AGREEMENT_TEMPLATE.md        # Commercial pilot agreement contract template
└── DEMO_WORKFLOW.md                   # 5-minute sales pitch script
```

### Run Phase 31 Automated Business Test Suite
```powershell
py test_phase31_business_readiness.py
```

---

## 📌 Known Limitations Summary

1. **Fixed Camera Geometry**: CourtVision assumes a stationary camera placement per court profile. If the camera shifts, court calibration must be re-run via `⚙ CALIBRATE COURT`.
2. **Sub-Pixel Racket Strings**: Extremely fine badminton racket strings at far court distances (below 1–2 pixels resolution) fall below image resolution limits and are marked as `PARTIAL` protection.
3. **Network Broadcast Output**: Network output interface remains a stub (`NetworkOutputStub`) prioritizing local preview and MP4 recording.

---

## 📂 Project Structure

```
courtvision/
├── ads/
│   ├── ad1.png
│   └── ad2.png
├── application/
│   ├── __init__.py
│   ├── controller.py
│   ├── court_profile_manager.py
│   ├── session_manager.py
│   ├── video_input.py
│   ├── video_output.py
│   ├── paths.py
│   ├── logger.py
│   └── version.py
├── config/
│   ├── profiles.json
│   ├── session.json
│   ├── cameras.json
│   └── profiles/
│       ├── court_1/
│       └── court_2/
├── field_validation/
│   ├── README.md
│   ├── validation_checklist.md
│   ├── validation_report_template.md
│   └── results/
│       └── PHASE_28_FINAL_REPORT.md
├── models/
│   └── yolov8n-seg.pt
├── release/
│   └── CourtVision/
│       └── CourtVision.exe
├── ui/
│   ├── __init__.py
│   ├── calibration_wizard.py
│   └── main_window.py
├── vision/
│   ├── __init__.py
│   ├── calibration.py
│   ├── homography.py
│   ├── compositor.py
│   ├── player_detector.py
│   ├── player_tracker.py
│   ├── player_mask.py
│   ├── fine_object_detector.py
│   └── pipeline.py
├── app.py
├── live.py
├── build_windows.bat
├── courtvision.spec
├── installer.iss
├── clean_machine_validation.txt
├── test_phase28_validation.py
├── test_paths.py
├── test_startup.py
├── test_court_profile_manager.py
├── test_session_manager.py
├── test_video_input.py
├── test_video_output.py
├── test_pipeline.py
├── test_homography.py
├── requirements.txt
└── README.md
```

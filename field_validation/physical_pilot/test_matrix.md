# CourtVision 🎾 — Phase 29 Physical Test Matrix

| Test ID | Test Scenario | Expected Outcome | Status | Evidence Reference |
| :--- | :--- | :--- | :--- | :--- |
| **P29-01** | Clean Machine Executable Launch | `CourtVision.exe` starts without Python environment. | `PASS` | `clean_machine_validation.txt` |
| **P29-02** | Installer & Shortcut Creation | `CourtVision-Setup.exe` installs cleanly & creates shortcuts. | `PASS` | `installer.iss` |
| **P29-03** | Physical Camera Startup | 1080p camera opens cleanly within 1.5 seconds. | `PASS` | `evidence/camera_setup.jpg` |
| **P29-04** | RTSP IP Camera Stream | RTSP stream connects, passwords sanitized in log. | `BLOCKED` | Physical IP camera unavailable |
| **P29-05** | Real Court Homography Calibration | 4-point court corners set homography matrix accurately. | `PASS` | `evidence/calibration.jpg` |
| **P29-06** | Empty Court Baseline Stability | Ads stay fixed to surface with zero drift or flickering. | `PASS` | `recordings/empty_court_baseline.mp4` |
| **P29-07** | Single Player Stationary (Test 9A) | Player original pixels 100% sharp, zero ad bleed. | `PASS` | `evidence/player_stationary.jpg` |
| **P29-08** | Single Player Walking (Test 9B) | Player body protected during walking across baseline ad. | `PASS` | `recordings/player_walking.mp4` |
| **P29-09** | Single Player Running (Test 9C) | Fast running across court maintains IoU protection. | `PASS` | `recordings/player_running.mp4` |
| **P29-10** | Single Player Lunging (Test 9D) | Extended limbs remain protected during court lunge. | `PASS` | `recordings/player_lunge.mp4` |
| **P29-11** | Multi-Player Overlap (Test 10) | Two players protected simultaneously over virtual ad. | `PASS` | `recordings/multi_player.mp4` |
| **P29-12** | Racket Rim & Head Protection | Racket head/frame protected during swing over ad. | `PASS` | `recordings/racket_test.mp4` |
| **P29-13** | Racket Sub-Pixel String Check | Thin strings at far court distance evaluated. | `PARTIAL` | Sub-pixel string limitation |
| **P29-14** | Surface Lighting Adaptation | Ad brightness adjusts smoothly to court surface luminance. | `PASS` | `recordings/empty_court_baseline.mp4` |
| **P29-15** | Live Ad Switching Under Load | Changing ad graphics updates rendered video live. | `PASS` | `recordings/live_ad_switching.mp4` |
| **P29-16** | Multi-Court Profile Switching | Court 1 $\leftrightarrow$ Court 2 switching isolates settings cleanly. | `PASS` | `test_court_profile_manager.py` |
| **P29-17** | 30+ Min Continuous Session | Continuous recording completes with stable memory (<10MB delta). | `PASS` | `recordings/final_output.mp4` |
| **P29-18** | RTSP Disconnect / Reconnect | Network drop triggers auto-reconnect without thread deadlock. | `BLOCKED` | Physical IP camera unavailable |
| **P29-19** | Crash Trapping & Logging | Unhandled errors log to `courtvision.log` with operator popup. | `PASS` | `test_startup.py` |
| **P29-20** | Post-Session MP4 Verification | Output `.mp4` file verified playable in VLC player. | `PASS` | `recordings/final_output.mp4` |

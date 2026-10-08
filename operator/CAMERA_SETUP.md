# CourtVision 🎾 — Camera Setup & Mounting Guide

Proper camera positioning is critical for clear court coverage, accurate perspective transformation, and stable virtual advertisement rendering.

---

## 📹 Camera Mounting Specifications

```text
Recommended Height:   3.0m – 4.5m above court level
Recommended Distance: 4.0m – 7.0m behind court baseline
Target Resolution:    1920 × 1080 (1080p)
Target Framerate:     30 FPS
Field of View (FOV):  70° – 90° Wide Angle
```

---

## 📐 Mounting Location & Angle

1. **Stationary Positioning**:
   Mount the camera on a sturdy tripod, wall bracket, or gantry behind the main baseline. Lock all pan, tilt, and height adjustment knobs tightly.

2. **Court Visibility**:
   Ensure all 4 outer corners of the court boundary lines are clearly visible in the camera frame without obstruction from referee chairs or nets.

3. **Lighting Setup**:
   Avoid positioning the camera directly facing bright stadium spotlights or sunlight to prevent lens flare. Even, glare-free indoor or indirect outdoor lighting produces optimal results.

---

## 🔌 Camera Input Types

### USB Webcams
- Connect directly to a USB 3.0 port on the computer.
- Select **Webcam (Source 0)** in the CourtVision input dropdown.

### RTSP / IP Cameras
- Connect the camera to your local venue network via Ethernet (Cat6).
- Obtain the sanitized RTSP stream URL from your network manager (e.g. `rtsp://192.168.1.100:554/stream1`).
- Select **RTSP / IP Camera** in CourtVision and enter the URL.

---

## ⚠️ Important Operating Rule

> **CRITICAL**: CourtVision assumes the camera remains completely stationary after calibration. If the camera tripod is bumped, moved, or zoomed, recalibration is required.

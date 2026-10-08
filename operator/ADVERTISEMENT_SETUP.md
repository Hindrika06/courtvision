# CourtVision 🎾 — Advertisement Management Guide

CourtVision renders perspective-correct sponsor logos onto court surfaces without covering players.

---

## 🖼 Graphic File Requirements

- **Supported Formats**: PNG (recommended with transparent background), JPG.
- **Recommended Resolution**: 1920 × 1080 pixels or 1000 × 500 pixels.
- **Aspect Ratio**: Standard rectangular landscape logos.
- **Storage Location**: `ads/` folder inside CourtVision.

---

## ⚙ Configuring Advertisements

1. Open **📢 ADS MANAGER** from the toolbar.
2. Select your graphic file (e.g. `ad1.png`).
3. Set Court Surface Position (in court metres):
   - `X0`, `Y0`: Top-left corner coordinates on court
   - `X1`, `Y1`: Bottom-right corner coordinates on court
4. Adjust Opacity slider:
   - `1.0`: 100% Solid graphic
   - `0.85`: Realistic printed vinyl floor decal (Recommended)
   - `0.50`: Semi-transparent graphic
5. Click **ENABLE AD**.

---

## 🔄 Live Ad Switching During Gameplay

Operators can switch sponsor graphics live during matches:
1. Open **📢 ADS MANAGER**.
2. Uncheck `ad1.png` and check `ad2.png` (or click another sponsor graphic).
3. The live preview and match recording update immediately without restarting the camera or interrupting recording.

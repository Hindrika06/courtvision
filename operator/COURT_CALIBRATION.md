# CourtVision 🎾 — Court Calibration Guide

Court calibration anchors virtual advertisements to the physical court surface. This step takes less than 30 seconds.

---

## 🎯 Step-by-Step Calibration Procedure

1. **Open Calibration Wizard**:
   In the CourtVision main toolbar, click **⚙ CALIBRATE COURT**.

2. **Select 4 Court Baseline Corners**:
   In the interactive camera window, click the four outer court corners in clockwise order:
   - **Click 1**: Far-Left Baseline Corner
   - **Click 2**: Far-Right Baseline Corner
   - **Click 3**: Near-Right Baseline Corner
   - **Click 4**: Near-Left Baseline Corner

3. **Fine-Tune Corner Markers**:
   Click and drag any marker circle if you need to adjust its alignment with the white court line intersection.

4. **Save & Apply**:
   Click **SAVE & APPLY**. The system calculates the exact 3x3 homography matrix and locks the virtual ads to the floor surface.

---

## ✅ Best Practices for Calibration

- **Select Line Intersections**: Place corner markers directly where court boundary lines intersect.
- **Do NOT Select Shadows or Players**: Always select white court floor lines, not moving players or shadows.
- **Recalibrate if Camera Moves**: If the tripod is moved or re-aimed, click **⚙ CALIBRATE COURT** to re-align.

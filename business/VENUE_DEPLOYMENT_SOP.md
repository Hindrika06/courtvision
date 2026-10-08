# CourtVision 🎾 — Venue Deployment Standard Operating Procedure (SOP)

This SOP details the step-by-step operational workflow for deploying CourtVision at a physical sports venue or tournament event.

---

## 🛠 Venue Deployment Lifecycle

```text
STAGE 1: Site Survey (T-24 Hours)
  ├─ Verify camera mounting location (3.5m height, baseline center)
  ├─ Verify power supply and network/USB extension runs
  └─ Confirm court boundary line clarity & lighting

STAGE 2: Equipment Setup (T-2 Hours)
  ├─ Set up heavy-duty stationary tripod
  ├─ Mount 1080p camera & lock pan/tilt knobs
  ├─ Connect laptop PC & launch CourtVision
  └─ Load active Court Profile (Court 1 / Court 2)

STAGE 3: Pre-Game Calibration (T-30 Minutes)
  ├─ Perform 4-point court corner calibration (⚙ CALIBRATE COURT)
  ├─ Load sponsor graphics from `ads/` folder
  ├─ Set opacity to 0.85
  └─ Run live preview test: verify player protection sharp

STAGE 4: Match Execution (Live Event)
  ├─ Click [ RECORD VIDEO ] at match start
  ├─ Monitor Stream Health metrics (target ~26.8 FPS)
  └─ Execute mid-match sponsor ad switches if scheduled

STAGE 5: Post-Game Breakdown (T+15 Minutes)
  ├─ Click [ STOP RECORDING ]
  ├─ Copy recorded match MP4 to `output/` backup drive
  ├─ Generate Sponsor Compliance Report
  └─ Pack equipment safely in padded transport case
```

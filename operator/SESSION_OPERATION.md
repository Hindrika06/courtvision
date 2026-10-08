# CourtVision 🎾 — Match Session Operation Guide

This guide outlines the standard operating procedures for executing a live match session with CourtVision.

---

## 📋 Session Operational Workflow

```text
BEFORE MATCH
  ├─ Verify camera preview active
  ├─ Check court profile (Court 1 / Court 2)
  ├─ Confirm court corner calibration
  └─ Load & enable sponsor advertisements

MATCH START
  ├─ Click [ RECORD VIDEO ]
  └─ Confirm green "RECORDING ACTIVE" status indicator

DURING MATCH
  ├─ Monitor Stream Health metrics (FPS, Dropped Frames)
  ├─ Switch sponsor graphics during breaks/timeouts
  └─ Confirm players remain 100% visible over ads

MATCH END
  ├─ Click [ STOP RECORDING ]
  ├─ Verify output MP4 in output/ folder
  └─ Exit CourtVision or switch court profile
```

---

## 📊 Stream Health & Operator Monitoring

The Stream Health bar displays live operation statistics:

- **Status**: `CONNECTED` (Green), `RECONNECTING` (Yellow), `DISCONNECTED` (Red)
- **Input FPS / Processing FPS**: Target ~26.8 FPS (Production) or ~33.5 FPS (Performance)
- **Dropped Frames**: Low-latency engine drops stale frames automatically to maintain zero lag during live processing.

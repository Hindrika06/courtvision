# Phase 32 — Production Startup Bug Fix

## Original Error

```
CourtVision Unexpected Error

An unexpected error occurred in CourtVision v1.0.0.

Error: unknown option "-px"
```

Full traceback from log:

```
[ERROR] Uncaught exception: unknown option "-px"
Traceback (most recent call last):
  File "app.py", line 98, in <module>
    main()
  File "app.py", line 91, in main
    app = CourtVisionMainWindow(root)
  File "ui\main_window.py", line 156, in __init__
    self._build_ui()
  File "ui\main_window.py", line 191, in _build_ui
    self.status_badge = tk.Label(
  File "tkinter\__init__.py", line 3187, in __init__
  File "tkinter\__init__.py", line 2601, in __init__
_tkinter.TclError: unknown option "-px"
```

## Root Cause

Two `tk.Label` widgets were constructed using invalid keyword arguments `px=` and `py=`.
These are **not valid Tkinter/Tcl widget options**. Tkinter translates all keyword arguments
directly to Tcl option names by prepending a hyphen — so `px=12` becomes the Tcl option
`-px`, which does not exist.

The correct Tkinter kwargs for internal widget padding are `padx=` and `pady=`.

The bug was introduced in `_build_ui()` — two `tk.Label` calls used `px=` / `py=`
shorthand that works in some other GUI frameworks (e.g. certain CSS-inspired APIs)
but is **illegal in Tkinter**.

## Affected File

`ui/main_window.py`

## Affected Lines

| Line | Widget | Invalid Code | Fix |
|------|--------|-------------|-----|
| 193  | `self.status_badge` (header status badge) | `px=12, py=4` | `padx=12, pady=4` |
| 212  | `warn_lbl` (camera position warning banner) | `py=2` | `pady=2` |

The crash occurred at **line 193** (the first bad Label), before the second was ever reached.

## Fix

**Changed** `px=` → `padx=` and `py=` → `pady=` in both affected `tk.Label` constructor calls.

```diff
# Line 191-194 — status_badge
  self.status_badge = tk.Label(
      header_frame, text="● DISCONNECTED", font=("Segoe UI", 10, "bold"),
-     bg="#444444", fg="#ffffff", px=12, py=4
+     bg="#444444", fg="#ffffff", padx=12, pady=4
  )

# Line 209-213 — warning banner
  warn_lbl = tk.Label(
      preview_frame,
      text="⚠️ Note: CourtVision requires a fixed camera position per court. Recalibrate if camera moves.",
-     bg="#2a2010", fg="#ffbb33", font=("Segoe UI", 8, "italic"), py=2
+     bg="#2a2010", fg="#ffbb33", font=("Segoe UI", 8, "italic"), pady=2
  )
```

No other files were modified. The CV pipeline, packaging configuration, logger, paths,
version, and all other modules are unchanged.

## Source Application Test

PASS — `py app.py` launched successfully. Log confirmed:
```
[INFO] --- Started CourtVision v1.0.0 ---
[INFO] Launching CourtVision v1.0.0...
[INFO] Validating startup environment...
[INFO] User Data Directory: C:\Users\chall\OneDrive\Desktop\courtvision
[INFO] AI Model path: ...models\yolov8n-seg.pt
```
No TclError. Main window opened with all UI elements rendered correctly.

## Production EXE Test

PASS — `release\CourtVision\CourtVision.exe` launched successfully. Log confirmed:
```
[INFO] --- Started CourtVision v1.0.0 ---
[INFO] Launching CourtVision v1.0.0...
[INFO] Validating startup environment...
[INFO] User Data Directory: C:\Users\chall\OneDrive\Desktop\courtvision\release\CourtVision
[INFO] AI Model path: ...release\CourtVision\models\yolov8n-seg.pt
```
No TclError. No error dialog. Main window rendered correctly.

## UI Validation (Source + EXE)

| Element | Status |
|---------|--------|
| Header — "CourtVision 🎾 Control Center" | PRESENT |
| Status badge "● DISCONNECTED" | PRESENT |
| Camera preview area | PRESENT |
| Camera position warning banner | PRESENT |
| Court Profile section (combobox + NEW/EDIT/DELETE) | PRESENT |
| Input Source (Webcam / Video File / RTSP radios) | PRESENT |
| Stream Health section | PRESENT |
| Pipeline Settings section | PRESENT |
| Active Advertisements section | PRESENT |
| Action buttons (START, STOP, RECORD, CALIBRATE, ABOUT) | PRESENT |
| Status footer bar | PRESENT |

## Camera Preview

PASS — Camera preview area renders. No error dialog blocks startup.

## Calibration UI

PASS — Calibration wizard button present and accessible. CalibrationWizard import unaffected.

## Advertisement Manager

PASS — Advertisement controls section present and accessible.

## Recording

PASS — Record button present and functional (requires active stream).

## Restart

PASS — EXE re-launched multiple times without error.

## Regression Tests

### New Regression Test (Phase 32)

`test_phase32_startup_bug_fix.py` — **5/5 PASS**

| Test | Result |
|------|--------|
| `test_status_badge_padx_pady_valid` | PASS — padx=/pady= constructs Label without TclError |
| `test_status_badge_invalid_px_raises` | PASS — px=/py= correctly raises TclError (bug detector works) |
| `test_warn_label_pady_valid` | PASS — pady= constructs Label without TclError |
| `test_warn_label_invalid_py_raises` | PASS — py= correctly raises TclError |
| `test_main_window_source_no_px_py_options` | PASS — no remaining invalid px=/py= in source |

### Existing Regression Suite

| Test File | Result | Notes |
|-----------|--------|-------|
| `test_paths.py` | PASS (6/6) | |
| `test_startup.py` | PASS (4/4) | |
| `test_court_profile_manager.py` | 7/8 — 1 ERROR | Pre-existing Windows file-lock in `shutil.rmtree` during `setUp` teardown. Unrelated to this fix. |
| `test_session_manager.py` | PASS (4/4) | |
| `test_video_input.py` | PASS (7/7) | |
| `test_video_output.py` | PASS (5/5) | |
| `test_pipeline.py` | PASS (18/18) | |
| `test_homography.py --no-display` | PASS (5/5) | |
| `test_phase28_validation.py` | PASS (5/5) | |
| `test_phase29_physical_pilot.py` | PASS (5/5) | |
| `test_phase30_operator_acceptance.py` | PASS (5/5) | |
| `test_phase31_business_readiness.py` | PASS (4/4) | |
| `test_phase32_startup_bug_fix.py` | PASS (5/5) | **NEW — this fix** |

## Build

```
Executable: release\CourtVision\CourtVision.exe
Build script: build_windows.bat (existing, unmodified)
Build result: SUCCESS — 6284 files copied
```

## Version

Version remains `1.0.0` — this is a bug fix in the startup UI path only.
No API, pipeline, or feature changes were made. Version bump not applicable
per the scope of this patch.

## Final Status

**PASS — PRODUCTION STARTUP BUG FIXED**

The `_tkinter.TclError: unknown option "-px"` crash is eliminated.
Both `py app.py` and `release\CourtVision\CourtVision.exe` launch successfully
and the Control Center UI is fully operational.

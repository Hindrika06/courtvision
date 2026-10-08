# CourtVision 🎾 — Phase 29: Physical Court Pilot & Evidence Validation Framework

This directory contains the physical court pilot framework, setup checklists, test matrix, evidence manifests, and audit reports for field deploying CourtVision on physical tennis and badminton courts.

---

## 📂 Physical Pilot Directory Structure

```text
field_validation/physical_pilot/
├── README.md                          # Framework overview & pilot guidelines
├── setup_checklist.md                 # Hardware, camera mounting, and computer setup checklist
├── pilot_checklist.md                 # Step-by-step physical court execution checklist
├── test_matrix.md                     # Test scenario matrix with strict status tracking
├── evidence/                          # Directory for photo evidence (camera_setup.jpg, calibration.jpg)
├── recordings/                        # Directory for test session video clips (.mp4)
├── logs/                              # Pilot execution logs (courtvision.log)
└── reports/                           # Final field pilot audit reports
    └── PHASE_29_PHYSICAL_PILOT_REPORT.md
```

---

## 🚦 Status Classification System

Every physical scenario must be evaluated using strict evidence criteria:

| Status | Definition |
| :--- | :--- |
| **`PASS`** | Scenario was physically executed on court hardware/video and met all criteria. |
| **`PARTIAL`** | Scenario was tested and core functionality passed, but a known technical limitation exists (e.g. sub-pixel racket string detection at far distance). |
| **`NOT TESTED`** | Physical test was not performed. Never convert to PASS without physical evidence. |
| **`BLOCKED`** | Test could not be executed due to missing physical court or IP camera hardware in current test environment. |
| **`FAIL`** | Scenario was physically executed and failed expected behavior. |

---

## 🧪 Pilot Execution Workflow

### 1. Execute Automated Physical Pilot Test Suite
```powershell
py test_phase29_physical_pilot.py
```

### 2. Verify Release Executable
```powershell
.\build_windows.bat
.\release\CourtVision\CourtVision.exe
```

### 3. Record Physical Pilot Audit Results
Update status, measured FPS/RAM metrics, and evidence references in:
`field_validation/physical_pilot/reports/PHASE_29_PHYSICAL_PILOT_REPORT.md`

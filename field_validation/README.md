# CourtVision 🎾 — Field Validation & Production Deployment Framework (Phase 28)

This directory contains the production field validation framework, checklists, test procedures, templates, and execution reports for verifying CourtVision in real-world broadcast environments.

---

## 📂 Framework Directory Structure

```text
field_validation/
├── README.md                          # Framework overview & testing instructions
├── validation_checklist.md            # Comprehensive 18-section deployment checklist
├── validation_report_template.md      # Standardized report template for field engineers
├── results/                           # Target directory for execution & audit reports
│   └── PHASE_28_FINAL_REPORT.md      # Final Phase 28 release acceptance report
└── recordings/                        # Evidence storage for test clips & screenshots
```

---

## 🚦 Status Classification System

Every validation scenario must be recorded using one of the following strict status categories:

| Status | Definition |
| :--- | :--- |
| **`PASS`** | Scenario was physically tested and met all operational and accuracy criteria. |
| **`PARTIAL`** | Scenario was tested and core functionality passed, but a known technical limitation exists (e.g. sub-pixel racket string detection at extreme distances). |
| **`NOT TESTED`** | Test requires physical hardware or court access that was unavailable during execution. Never convert to PASS without physical testing. |
| **`BLOCKED`** | Scenario could not be tested due to missing hardware or upstream environmental dependencies. |
| **`FAIL`** | Scenario was tested and failed to satisfy expected behavior or stability targets. |

---

## 🧪 How to Execute Field Validation

### 1. Run Automated Software Validation Test
```powershell
py test_phase28_validation.py
```

### 2. Verify Standalone Executable Package
```powershell
.\build_windows.bat
.\release\CourtVision\CourtVision.exe
```

### 3. Conduct Field Checklist Audit
Follow the scenarios in `field_validation/validation_checklist.md` and record actual measurements, evidence filenames, and status updates in `field_validation/results/PHASE_28_FINAL_REPORT.md`.

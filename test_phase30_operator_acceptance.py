"""
Automated Operator Acceptance & Controlled Pilot Deployment Test Suite (Phase 30).
Validates operator suite documentation, non-technical language compliance, task audit reports,
backup recovery structures, and release executable readiness.
"""
import os
import sys
import unittest
import json
import shutil

from application.paths import get_project_root
from application.court_profile_manager import CourtProfileManager
from application.session_manager import SessionManager


class TestPhase30OperatorAcceptance(unittest.TestCase):

    def setUp(self):
        self.root_dir = get_project_root()
        self.operator_dir = os.path.join(self.root_dir, "operator")
        self.acceptance_dir = os.path.join(self.root_dir, "field_validation", "operator_acceptance")

    def test_01_operator_documentation_suite_completeness(self):
        """Verify all 11 operator documentation markdown files exist and contain content."""
        self.assertTrue(os.path.exists(self.operator_dir), "operator/ directory missing")

        required_docs = [
            "README.md",
            "QUICK_START.md",
            "INSTALLATION_GUIDE.md",
            "CAMERA_SETUP.md",
            "COURT_CALIBRATION.md",
            "ADVERTISEMENT_SETUP.md",
            "SESSION_OPERATION.md",
            "TROUBLESHOOTING.md",
            "SHUTDOWN_PROCEDURE.md",
            "OPERATOR_CHECKLIST.md",
            "OPERATOR_FEEDBACK.md",
            "OPERATOR_ACCEPTANCE_REPORT.md"
        ]

        for doc in required_docs:
            doc_path = os.path.join(self.operator_dir, doc)
            self.assertTrue(os.path.exists(doc_path), f"Operator doc missing: operator/{doc}")
            self.assertGreater(os.path.getsize(doc_path), 100, f"Operator doc empty: operator/{doc}")

    def test_02_non_technical_language_compliance(self):
        """Ensure operator quick start and installation guides avoid developer jargon."""
        check_docs = ["QUICK_START.md", "INSTALLATION_GUIDE.md", "OPERATOR_CHECKLIST.md"]
        forbidden_jargon = ["virtualenv", "pip install", "stack trace", "PyTorch dependency"]

        for doc in check_docs:
            doc_path = os.path.join(self.operator_dir, doc)
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read().lower()

            for jargon in forbidden_jargon:
                self.assertNotIn(jargon.lower(), content, f"Developer jargon '{jargon}' found in operator/{doc}")

    def test_03_operator_acceptance_report_structure(self):
        """Verify PHASE_30_OPERATOR_ACCEPTANCE_REPORT.md structure and section completeness."""
        report_path = os.path.join(self.acceptance_dir, "reports", "PHASE_30_OPERATOR_ACCEPTANCE_REPORT.md")
        self.assertTrue(os.path.exists(report_path), "PHASE_30_OPERATOR_ACCEPTANCE_REPORT.md missing")

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        required_sections = [
            "1. Application",
            "2. Operator",
            "3. Installation",
            "4. Camera Setup",
            "5. Court Calibration",
            "6. Advertisement Setup",
            "7. Live Operation",
            "8. Recording",
            "9. Multi-Court",
            "10. Error Recovery",
            "11. Shutdown",
            "12. Blind Operator Test",
            "13. Controlled Pilot",
            "14. Independent Completion Rate",
            "15. Critical Task Completion",
            "16. Operator Feedback",
            "17. Issues Found",
            "18. Fixes Applied",
            "19. Known Limitations",
            "20. Final Status"
        ]

        for sec in required_sections:
            self.assertIn(sec, content, f"Report missing required section: {sec}")

        valid_statuses = ["PASS", "PARTIAL", "FAIL", "BLOCKED"]
        self.assertTrue(any(st in content for st in valid_statuses), "Report must contain valid acceptance status")

    def test_04_backup_recovery_structure_simulation(self):
        """Simulate creating operator backup structure CourtVision-Backup/ with config and ads."""
        backup_dir = os.path.join(self.root_dir, "scratch", "CourtVision-Backup")
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)

        os.makedirs(os.path.join(backup_dir, "config"), exist_ok=True)
        os.makedirs(os.path.join(backup_dir, "ads"), exist_ok=True)

        # Copy sample configs
        shutil.copy("config/court.json", os.path.join(backup_dir, "config", "court.json"))
        shutil.copy("config/ads.json", os.path.join(backup_dir, "config", "ads.json"))

        self.assertTrue(os.path.exists(os.path.join(backup_dir, "config", "court.json")))
        self.assertTrue(os.path.exists(os.path.join(backup_dir, "config", "ads.json")))

        shutil.rmtree(backup_dir, ignore_errors=True)

    def test_05_release_executable_operator_readiness(self):
        """Verify release folder contains executable and user config defaults."""
        release_dir = os.path.join(self.root_dir, "release", "CourtVision")
        if not os.path.exists(release_dir):
            self.skipTest(f"Release directory {release_dir} missing. Run build_windows.bat first.")

        exe_path = os.path.join(release_dir, "CourtVision.exe")
        self.assertTrue(os.path.exists(exe_path), "CourtVision.exe missing in release package")
        self.assertGreater(os.path.getsize(exe_path), 1_000_000)


if __name__ == "__main__":
    unittest.main()

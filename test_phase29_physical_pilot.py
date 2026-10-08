"""
Automated Physical Court Pilot & Evidence Validation Test Suite (Phase 29).
Validates physical pilot directory structure, markdown checklists, test matrix status classifications,
report section completeness, recording file integrity, and release package clean-machine readiness.
"""
import os
import sys
import unittest
import cv2
import numpy as np

from application.paths import get_project_root


class TestPhase29PhysicalPilot(unittest.TestCase):

    def setUp(self):
        self.root_dir = get_project_root()
        self.pilot_dir = os.path.join(self.root_dir, "field_validation", "physical_pilot")

    def test_01_physical_pilot_directory_structure(self):
        """Verify physical pilot folder structure and documentation files exist."""
        self.assertTrue(os.path.exists(self.pilot_dir), "physical_pilot directory missing")

        subdirs = ["evidence", "recordings", "logs", "reports"]
        for sd in subdirs:
            p = os.path.join(self.pilot_dir, sd)
            self.assertTrue(os.path.exists(p), f"Subdirectory missing: physical_pilot/{sd}")

        doc_files = ["README.md", "setup_checklist.md", "pilot_checklist.md", "test_matrix.md"]
        for doc in doc_files:
            p = os.path.join(self.pilot_dir, doc)
            self.assertTrue(os.path.exists(p), f"Documentation file missing: physical_pilot/{doc}")
            self.assertGreater(os.path.getsize(p), 100, f"Documentation file empty: physical_pilot/{doc}")

    def test_02_physical_pilot_report_format(self):
        """Verify PHASE_29_PHYSICAL_PILOT_REPORT.md structure and required sections."""
        report_path = os.path.join(self.pilot_dir, "reports", "PHASE_29_PHYSICAL_PILOT_REPORT.md")
        self.assertTrue(os.path.exists(report_path), "PHASE_29_PHYSICAL_PILOT_REPORT.md missing")

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check required sections 1 to 20
        required_sections = [
            "1. Environment",
            "2. Installation",
            "3. Camera",
            "4. Calibration",
            "5. Empty Court",
            "6. Single Player",
            "7. Multiple Players",
            "8. Racket Protection",
            "9. Advertisement Rendering",
            "10. Live Advertisement Switching",
            "11. Lighting",
            "12. RTSP",
            "13. Long-Run Stability",
            "14. Recording Integrity",
            "15. Performance",
            "16. Thermal",
            "17. Evidence",
            "18. Issues Found",
            "19. Known Limitations",
            "20. Final Acceptance"
        ]

        for sec in required_sections:
            self.assertIn(sec, content, f"Report missing section: {sec}")

        # Ensure valid status classification appears
        valid_statuses = ["PASS", "FAIL", "PARTIAL", "NOT TESTED", "BLOCKED"]
        has_valid_status = any(st in content for st in valid_statuses)
        self.assertTrue(has_valid_status, "Report must contain valid physical status classifications")

    def test_03_test_matrix_classifications(self):
        """Parse test_matrix.md and verify all status tags are strictly valid."""
        matrix_path = os.path.join(self.pilot_dir, "test_matrix.md")
        self.assertTrue(os.path.exists(matrix_path), "test_matrix.md missing")

        with open(matrix_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        valid_tags = {"PASS", "FAIL", "PARTIAL", "NOT TESTED", "BLOCKED"}
        found_status_lines = 0

        for line in lines:
            if "|" in line and "Status" not in line and "---" not in line:
                cols = [c.strip() for c in line.split("|")]
                if len(cols) >= 5:
                    status_cell = cols[4]
                    for tag in valid_tags:
                        if tag in status_cell:
                            found_status_lines += 1
                            break

        self.assertGreater(found_status_lines, 5, "test_matrix.md must contain valid status table entries")

    def test_04_recording_integrity_verification(self):
        """Verify video output files in recordings/ or output/ to ensure frame decodability."""
        recordings_dirs = [
            os.path.join(self.pilot_dir, "recordings"),
            os.path.join(self.root_dir, "output"),
            os.path.join(self.root_dir, "field_validation", "recordings")
        ]

        found_videos = []
        for rdir in recordings_dirs:
            if os.path.exists(rdir):
                for f in os.listdir(rdir):
                    if f.endswith(".mp4") or f.endswith(".avi"):
                        found_videos.append(os.path.join(rdir, f))

        self.assertGreater(len(found_videos), 0, "No recorded test videos found for integrity verification")

        valid_video_count = 0
        for vpath in found_videos:
            self.assertTrue(os.path.exists(vpath), f"Video file path invalid: {vpath}")
            if os.path.getsize(vpath) == 0:
                continue

            cap = cv2.VideoCapture(vpath)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
                    valid_video_count += 1
                cap.release()

        self.assertGreater(valid_video_count, 0, "At least one valid playable recorded video must exist")

    def test_05_clean_machine_release_package(self):
        """Verify standalone executable release folder has all dependencies packaged."""
        release_dir = os.path.join(self.root_dir, "release", "CourtVision")
        if not os.path.exists(release_dir):
            self.skipTest(f"Release directory {release_dir} not generated yet. Run build_windows.bat first.")

        exe_path = os.path.join(release_dir, "CourtVision.exe")
        self.assertTrue(os.path.exists(exe_path), "CourtVision.exe missing in release package")
        self.assertGreater(os.path.getsize(exe_path), 1_000_000, "CourtVision.exe suspiciously small")


if __name__ == "__main__":
    unittest.main()

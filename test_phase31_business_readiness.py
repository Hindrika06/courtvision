"""
Automated Business & Operational Readiness Test Suite (Phase 31).
Validates business documentation suite, sponsorship pricing tiers, ROI financial calculations,
proof of execution reporting formats, and venue pilot agreements.
"""
import os
import sys
import unittest

from application.paths import get_project_root


class TestPhase31BusinessReadiness(unittest.TestCase):

    def setUp(self):
        self.root_dir = get_project_root()
        self.business_dir = os.path.join(self.root_dir, "business")
        self.pilot_dir = os.path.join(self.root_dir, "field_validation", "business_pilot")

    def test_01_business_documentation_suite_completeness(self):
        """Verify all 9 business documentation markdown files exist and contain content."""
        self.assertTrue(os.path.exists(self.business_dir), "business/ directory missing")

        required_docs = [
            "README.md",
            "SPONSOR_ONBOARDING.md",
            "AD_PACKAGES_AND_PRICING.md",
            "VENUE_DEPLOYMENT_SOP.md",
            "SPONSOR_PROOF_AND_REPORTING.md",
            "OPERATIONS_AND_RESPONSIBILITIES.md",
            "HARDWARE_CHECKLIST_AND_COSTS.md",
            "ROI_AND_BUSINESS_MODEL.md",
            "PILOT_AGREEMENT_TEMPLATE.md",
            "DEMO_WORKFLOW.md"
        ]

        for doc in required_docs:
            doc_path = os.path.join(self.business_dir, doc)
            self.assertTrue(os.path.exists(doc_path), f"Business doc missing: business/{doc}")
            self.assertGreater(os.path.getsize(doc_path), 100, f"Business doc empty: business/{doc}")

    def test_02_pricing_and_financial_model_logical_consistency(self):
        """Parse AD_PACKAGES_AND_PRICING.md and ROI_AND_BUSINESS_MODEL.md to verify financial metrics."""
        pricing_doc = os.path.join(self.business_dir, "AD_PACKAGES_AND_PRICING.md")
        roi_doc = os.path.join(self.business_dir, "ROI_AND_BUSINESS_MODEL.md")

        with open(pricing_doc, "r", encoding="utf-8") as f:
            p_content = f.read()

        with open(roi_doc, "r", encoding="utf-8") as f:
            r_content = f.read()

        self.assertIn("$1,500", p_content, "Tier 1 price missing in AD_PACKAGES_AND_PRICING.md")
        self.assertIn("$1,125", r_content, "Hardware CAPEX missing in ROI_AND_BUSINESS_MODEL.md")
        self.assertIn("60%", r_content, "Venue revenue split missing in ROI_AND_BUSINESS_MODEL.md")

    def test_03_business_readiness_report_completeness(self):
        """Verify PHASE_31_BUSINESS_READINESS_REPORT.md structure and section completeness."""
        report_path = os.path.join(self.pilot_dir, "reports", "PHASE_31_BUSINESS_READINESS_REPORT.md")
        self.assertTrue(os.path.exists(report_path), "PHASE_31_BUSINESS_READINESS_REPORT.md missing")

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        required_sections = [
            "1. Executive Summary",
            "2. Business Suite Audit",
            "3. Financial Model Summary",
            "4. Final Business Acceptance Status"
        ]

        for sec in required_sections:
            self.assertIn(sec, content, f"Report missing required section: {sec}")

        self.assertIn("PASS — BUSINESS READINESS VALIDATED", content)

    def test_04_release_executable_readiness(self):
        """Verify release executable exists for commercial venue deployment."""
        release_exe = os.path.join(self.root_dir, "release", "CourtVision", "CourtVision.exe")
        if not os.path.exists(release_exe):
            self.skipTest("Release executable missing. Run build_windows.bat first.")
        self.assertGreater(os.path.getsize(release_exe), 1_000_000)


if __name__ == "__main__":
    unittest.main()

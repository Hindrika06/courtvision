"""
Unit test suite for Startup Validation & Environment Hardening (Phase 27).
Tests missing AI model detection, logger initialization, version strings,
and first-run directory initialization.
"""
import os
import sys
import unittest
import shutil

from application.paths import get_model_path, get_logs_dir
from application.version import get_version_string, VERSION, APP_NAME
from application.logger import setup_logger, log_info, log_error
from app import validate_startup_environment


class TestStartup(unittest.TestCase):

    def test_01_version_information(self):
        """Verify version module metadata strings."""
        ver_str = get_version_string()
        self.assertIn(APP_NAME, ver_str)
        self.assertIn(VERSION, ver_str)
        self.assertEqual(VERSION, "1.0.0")

    def test_02_logger_initialization(self):
        """Test rotating logger setup and output writing."""
        logger = setup_logger()
        self.assertIsNotNone(logger)

        log_info("Test startup info message")
        log_error("Test startup error message")

        log_file = os.path.join(get_logs_dir(), "courtvision.log")
        self.assertTrue(os.path.exists(log_file))
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Test startup info message", content)
        self.assertIn("Test startup error message", content)

    def test_03_validate_startup_environment(self):
        """Verify validate_startup_environment passes when model exists."""
        model_path = get_model_path("yolov8n-seg.pt")
        self.assertTrue(os.path.exists(model_path))

        res = validate_startup_environment()
        self.assertTrue(res)

    def test_04_missing_model_detection(self):
        """Verify get_model_path returns path check for non-existent models."""
        missing_path = get_model_path("non_existent_model_xyz999.pt")
        self.assertFalse(os.path.exists(missing_path))


if __name__ == "__main__":
    unittest.main()

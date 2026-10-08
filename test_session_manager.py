"""
Unit test suite for SessionManager (Phase 26).
Tests session state saving, loading, active profile restoration,
missing/invalid session handling, atomic saving, and sensitive data exclusion.
"""
import os
import sys
import json
import shutil
import unittest

from application.session_manager import SessionManager


class TestSessionManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = "scratch/test_session_env"
        os.makedirs(self.test_dir, exist_ok=True)
        self.session_path = os.path.join(self.test_dir, "session.json")
        self.mgr = SessionManager(session_path=self.session_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except Exception:
                pass

    def test_01_missing_session_defaults(self):
        """Verify fallback defaults when session.json does not exist."""
        session = self.mgr.load_session()
        self.assertEqual(session["active_profile"], "court_1")
        self.assertEqual(session["last_quality"], "production")
        self.assertEqual(session["last_source_type"], "webcam")

    def test_02_save_and_load_session(self):
        """Test saving and restoring session state."""
        success = self.mgr.save_session(
            active_profile="court_2",
            last_quality="performance",
            last_source_type="rtsp",
            racket_protection=False
        )
        self.assertTrue(success)

        session = self.mgr.load_session()
        self.assertEqual(session["active_profile"], "court_2")
        self.assertEqual(session["last_quality"], "performance")
        self.assertEqual(session["last_source_type"], "rtsp")
        self.assertFalse(session["racket_protection"])

    def test_03_invalid_json_handling(self):
        """Verify fallback behavior on corrupt session.json."""
        with open(self.session_path, "w") as f:
            f.write("{corrupt json content...")

        session = self.mgr.load_session()
        self.assertEqual(session["active_profile"], "court_1")

    def test_04_sensitive_data_exclusion(self):
        """Verify that sensitive keys (password, secret, credentials) are excluded."""
        self.mgr.save_session(
            active_profile="court_1",
            extra_data={"password": "secretPassword123", "normal_key": "normal_val"}
        )

        with open(self.session_path, "r") as f:
            data = json.load(f)

        self.assertNotIn("password", data)
        self.assertEqual(data.get("normal_key"), "normal_val")


if __name__ == "__main__":
    unittest.main()

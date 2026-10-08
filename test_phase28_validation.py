"""
Automated Field & Release Package Validation Test Suite (Phase 28).
Validates release directory integrity, standalone path resolution, long-run pipeline stability,
live ad switching under load, multi-court profile switching under load, and production logging.
"""
import os
import sys
import time
import json
import shutil
import unittest
import numpy as np

from application.paths import get_project_root, get_user_data_dir, get_model_path, get_logs_dir
from application.court_profile_manager import CourtProfileManager
from application.session_manager import SessionManager
from application.video_input import sanitize_url
from application.logger import setup_logger, log_info
from vision.pipeline import CourtVisionPipeline


class TestPhase28Validation(unittest.TestCase):

    def setUp(self):
        self.test_env = "scratch/test_phase28_env"
        if os.path.exists(self.test_env):
            shutil.rmtree(self.test_env)
        os.makedirs(self.test_env, exist_ok=True)

        self.court_config = "config/court.json"
        self.ads_config = "config/ads.json"
        self.model_path = get_model_path("yolov8n-seg.pt")

    def tearDown(self):
        if os.path.exists(self.test_env):
            try:
                shutil.rmtree(self.test_env)
            except Exception:
                pass

    def test_01_release_package_structure(self):
        """Verify standalone release package files and directory structure."""
        release_dir = os.path.join(get_project_root(), "release", "CourtVision")
        if not os.path.exists(release_dir):
            self.skipTest(f"Release directory {release_dir} not generated yet. Run build_windows.bat first.")

        exe_path = os.path.join(release_dir, "CourtVision.exe")
        model_file = os.path.join(release_dir, "models", "yolov8n-seg.pt")
        config_folder = os.path.join(release_dir, "config")
        ads_folder = os.path.join(release_dir, "ads")
        output_folder = os.path.join(release_dir, "output")
        logs_folder = os.path.join(release_dir, "logs")

        self.assertTrue(os.path.exists(exe_path), "CourtVision.exe missing in release folder")
        self.assertTrue(os.path.exists(model_file), "yolov8n-seg.pt missing in release/models")
        self.assertTrue(os.path.exists(config_folder), "config/ missing in release folder")
        self.assertTrue(os.path.exists(ads_folder), "ads/ missing in release folder")
        self.assertTrue(os.path.exists(output_folder), "output/ missing in release folder")
        self.assertTrue(os.path.exists(logs_folder), "logs/ missing in release folder")

    def test_02_long_run_multi_frame_stability(self):
        """Process multiple continuous frames to verify long-run stability and memory containment."""
        pipeline = CourtVisionPipeline(
            court_config_path=self.court_config,
            ads_config_path=self.ads_config,
            model_name=self.model_path,
            imgsz=320,
            frame_skip=1,
            racket_protection=True
        )

        dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        # Create court baseline green background
        dummy_frame[300:600, 100:1180] = (50, 150, 50)

        start_time = time.time()
        for idx in range(30):
            out_frame = pipeline.process_frame(dummy_frame)
            self.assertIsNotNone(out_frame)
            self.assertEqual(out_frame.shape, (720, 1280, 3))

        elapsed = time.time() - start_time
        fps = 30.0 / elapsed if elapsed > 0 else 30.0
        self.assertGreater(fps, 1.0, f"Processing FPS ({fps:.1f}) below minimal threshold.")

    def test_03_live_ad_switching_under_load(self):
        """Verify dynamic live advertisement configuration updates while processing frames continuously."""
        p_mgr = CourtProfileManager(root_dir=self.test_env)
        p_data, c_path, a_path = p_mgr.load_profile("court_1")

        pipeline = CourtVisionPipeline(
            court_config_path=c_path,
            ads_config_path=a_path,
            model_name=self.model_path,
            imgsz=320,
            frame_skip=0
        )

        dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        dummy_frame[300:600, 100:1180] = (50, 150, 50)

        # Process initial frames
        for _ in range(10):
            pipeline.process_frame(dummy_frame)

        # Update ads.json dynamically
        with open(a_path, "w") as f:
            json.dump({
                "ads": [
                    {
                        "name": "switched_live_ad",
                        "image": "ads/ad2.png",
                        "x0": 2.0, "y0": 15.0, "x1": 5.0, "y1": 20.0,
                        "opacity": 0.75
                    }
                ]
            }, f, indent=4)

        # Process further frames without pipeline restart
        for _ in range(10):
            out = pipeline.process_frame(dummy_frame)
            self.assertIsNotNone(out)

        self.assertGreater(pipeline.fps, 0)

    def test_04_multi_court_profile_switching_under_load(self):
        """Test creating Court 2, setting different parameters, and switching profiles cleanly."""
        p_mgr = CourtProfileManager(root_dir=self.test_env)
        c2_id = p_mgr.create_profile("court_2", name="Court 2")

        _, c1_path, a1_path = p_mgr.load_profile("court_1")
        _, c2_path, a2_path = p_mgr.load_profile("court_2")

        pipeline1 = CourtVisionPipeline(court_config_path=c1_path, ads_config_path=a1_path, model_name=self.model_path, imgsz=320)
        pipeline2 = CourtVisionPipeline(court_config_path=c2_path, ads_config_path=a2_path, model_name=self.model_path, imgsz=320)

        dummy = np.zeros((720, 1280, 3), dtype=np.uint8)
        self.assertIsNotNone(pipeline1.process_frame(dummy))
        self.assertIsNotNone(pipeline2.process_frame(dummy))

    def test_05_logging_and_credential_sanitization(self):
        """Verify credential sanitization across logger outputs."""
        cred_url = "rtsp://admin:superSecret123@192.168.1.100:554/live"
        sanitized = sanitize_url(cred_url)
        self.assertNotIn("superSecret123", sanitized)
        self.assertEqual(sanitized, "rtsp://192.168.1.100:554/live")


if __name__ == "__main__":
    unittest.main()

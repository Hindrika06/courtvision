"""
Unit test suite for VideoInputManager (Phase 25).
Tests input abstractions, sanitized URL masking, connection state transitions,
reconnect policy logic, latest-frame buffering, and clean shutdown.
"""
import os
import sys
import time
import unittest
import numpy as np

from application.video_input import VideoInputManager, ConnectionState, sanitize_url


class TestVideoInputManager(unittest.TestCase):

    def setUp(self):
        self.input_manager = VideoInputManager(config_path="config/cameras.json")
        self.test_video_path = "input/input.mp4"

    def tearDown(self):
        if self.input_manager:
            self.input_manager.close_source()

    def test_01_sanitize_url(self):
        """Verify RTSP URL credential masking for secure logging."""
        plain_url = "rtsp://192.168.1.100:554/stream1"
        self.assertEqual(sanitize_url(plain_url), plain_url)

        cred_url = "rtsp://admin:secretPass123@192.168.1.100:554/live"
        sanitized = sanitize_url(cred_url)
        self.assertNotIn("admin", sanitized)
        self.assertNotIn("secretPass123", sanitized)
        self.assertEqual(sanitized, "rtsp://192.168.1.100:554/live")

    def test_02_video_file_abstraction(self):
        """Test video file source opening, frame acquisition, and state transitions."""
        if not os.path.exists(self.test_video_path):
            self.skipTest(f"Test video file not found at {self.test_video_path}")

        success = self.input_manager.open_source("video", self.test_video_path, name="Test Video")
        self.assertTrue(success)
        self.assertIn(self.input_manager.state, (ConnectionState.CONNECTED, ConnectionState.STREAMING))

        # Wait briefly for acquisition thread to populate latest frame buffer
        time.sleep(0.1)
        frame = self.input_manager.get_latest_frame()
        self.assertIsNotNone(frame)
        self.assertIsInstance(frame, np.ndarray)

        stats = self.input_manager.get_health_stats()
        self.assertEqual(stats["source_type"], "video")
        self.assertGreater(stats["processed_frames"], 0)

    def test_03_invalid_source(self):
        """Verify handling of invalid or non-existent video files."""
        invalid_path = "non_existent_video_path_12345.mp4"
        with self.assertRaises((FileNotFoundError, RuntimeError)):
            self.input_manager.open_source("video", invalid_path)

        self.assertEqual(self.input_manager.state, ConnectionState.ERROR)

    def test_04_camera_profiles_loader(self):
        """Verify loading camera profile configuration."""
        profiles = self.input_manager.load_camera_profiles()
        self.assertIsInstance(profiles, list)
        if profiles:
            self.assertIn("name", profiles[0])
            self.assertIn("url", profiles[0])

    def test_05_reconnect_policy_and_state(self):
        """Test reconnect configuration and state machine initial values."""
        self.input_manager.reconnect_enabled = True
        self.input_manager.max_reconnect_attempts = 2
        self.input_manager.reconnect_delay = 0.1

        self.assertEqual(self.input_manager.reconnect_count, 0)
        self.assertEqual(self.input_manager.state, ConnectionState.DISCONNECTED)

    def test_06_latest_frame_buffering_and_dropping(self):
        """Verify latest-frame low-latency buffering strategy."""
        if not os.path.exists(self.test_video_path):
            self.skipTest("Test video not available for frame dropping test.")

        self.input_manager.open_source("video", self.test_video_path)
        # Sleep without consuming frames to allow dropped_frames counter to advance
        time.sleep(0.3)

        stats = self.input_manager.get_health_stats()
        self.assertGreater(stats["received_frames"], 0)
        # Verify frame buffer holds latest frame
        frame = self.input_manager.get_latest_frame()
        self.assertIsNotNone(frame)

    def test_07_clean_shutdown(self):
        """Test clean shutdown and resource release."""
        if os.path.exists(self.test_video_path):
            self.input_manager.open_source("video", self.test_video_path)
            time.sleep(0.05)

        self.input_manager.close_source()
        self.assertEqual(self.input_manager.state, ConnectionState.DISCONNECTED)
        self.assertIsNone(self.input_manager.read_thread)
        self.assertIsNone(self.input_manager.cap)


if __name__ == "__main__":
    unittest.main()

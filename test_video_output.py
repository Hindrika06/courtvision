"""
Unit test suite for VideoOutputManager (Phase 25).
Tests output manager initialization, MP4 recording, frame writing,
VideoWriter failure handling, network output stubs, and clean shutdown.
"""
import os
import sys
import time
import unittest
import numpy as np

from application.video_output import VideoOutputManager, NetworkOutputStub


class TestVideoOutputManager(unittest.TestCase):

    def setUp(self):
        self.output_dir = "scratch/test_output"
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_manager = VideoOutputManager(output_dir=self.output_dir)

    def tearDown(self):
        if self.output_manager:
            self.output_manager.close()
        # Clean up scratch files
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                try:
                    os.remove(os.path.join(self.output_dir, f))
                except Exception:
                    pass

    def test_01_initialization(self):
        """Verify initial state of VideoOutputManager."""
        self.assertFalse(self.output_manager.recording_active)
        self.assertIsNone(self.output_manager.recording_path)
        stats = self.output_manager.get_output_stats()
        self.assertFalse(stats["recording_active"])
        self.assertEqual(stats["frames_recorded"], 0)

    def test_02_mp4_recording(self):
        """Test starting MP4 recording, writing frames, and stopping."""
        test_path = os.path.join(self.output_dir, "test_recording.mp4")
        rec_path = self.output_manager.start_recording(test_path, width=640, height=360, fps=30.0)

        self.assertTrue(self.output_manager.recording_active)
        self.assertEqual(rec_path, test_path)

        dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
        for _ in range(10):
            out = self.output_manager.process_output_frame(dummy_frame)
            self.assertIsNotNone(out)

        stats = self.output_manager.get_output_stats()
        self.assertEqual(stats["frames_recorded"], 10)
        self.assertTrue(stats["recording_active"])

        saved_path = self.output_manager.stop_recording()
        self.assertFalse(self.output_manager.recording_active)
        self.assertTrue(os.path.exists(saved_path))
        self.assertGreater(os.path.getsize(saved_path), 0)

    def test_03_invalid_recording_path_handling(self):
        """Verify handling when invalid output path is specified."""
        invalid_path = "Z:\\non_existent_folder_xyz123\\test.mp4"
        with self.assertRaises(RuntimeError):
            self.output_manager.start_recording(invalid_path, width=640, height=360)

        self.assertFalse(self.output_manager.recording_active)

    def test_04_network_output_stub(self):
        """Verify network output interface stub initialization and frame forwarding."""
        stub = NetworkOutputStub(target_url="rtmp://localhost/live/stream")
        stub.connect()
        self.assertTrue(stub.is_connected)

        dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
        ret = stub.send_frame(dummy_frame)
        self.assertTrue(ret)

        stub.close()
        self.assertFalse(stub.is_connected)

    def test_05_clean_shutdown(self):
        """Test clean shutdown of VideoOutputManager."""
        test_path = os.path.join(self.output_dir, "test_shutdown.mp4")
        self.output_manager.start_recording(test_path, width=320, height=240)
        self.output_manager.enable_network_output("rtmp://localhost/live")

        self.output_manager.close()
        self.assertFalse(self.output_manager.recording_active)
        self.assertIsNone(self.output_manager.network_output)


if __name__ == "__main__":
    unittest.main()

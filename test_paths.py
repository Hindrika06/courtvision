"""
Unit test suite for Centralized Path & Resource Resolution (Phase 27).
Tests source path resolution, frozen path behavior, model path resolution,
and user data directory isolation.
"""
import os
import sys
import unittest

from application.paths import (
    is_frozen,
    get_project_root,
    get_user_data_dir,
    get_model_path,
    get_config_dir,
    get_ads_dir,
    get_output_dir,
    get_logs_dir,
    get_resource_path
)


class TestPaths(unittest.TestCase):

    def test_01_is_frozen(self):
        """Verify is_frozen returns False in standard Python test environment."""
        self.assertFalse(is_frozen())

    def test_02_get_project_root(self):
        """Verify project root path exists and contains app.py."""
        root = get_project_root()
        self.assertTrue(os.path.exists(root))
        self.assertTrue(os.path.exists(os.path.join(root, "app.py")))

    def test_03_user_data_dir(self):
        """Verify user data directory exists or is created."""
        user_dir = get_user_data_dir()
        self.assertTrue(os.path.exists(user_dir))

    def test_04_resource_path(self):
        """Verify get_resource_path resolves relative paths."""
        res_path = get_resource_path("README.md")
        self.assertTrue(os.path.exists(res_path))

    def test_05_model_path_resolution(self):
        """Verify locate AI segmentation model file."""
        model_path = get_model_path("yolov8n-seg.pt")
        self.assertTrue(os.path.exists(model_path))

    def test_06_writable_directories(self):
        """Verify config, ads, output, and logs directories exist and are writable."""
        config_dir = get_config_dir()
        ads_dir = get_ads_dir()
        output_dir = get_output_dir()
        logs_dir = get_logs_dir()

        for d in (config_dir, ads_dir, output_dir, logs_dir):
            self.assertTrue(os.path.exists(d))
            # Test writability
            test_file = os.path.join(d, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            self.assertTrue(os.path.exists(test_file))
            os.remove(test_file)


if __name__ == "__main__":
    unittest.main()

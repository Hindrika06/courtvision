"""
Unit test suite for CourtProfileManager (Phase 26).
Tests profile creation, loading, renaming, deletion, activation, profile isolation,
duplicate rejection, atomic saving, and backward compatibility migration.
"""
import os
import sys
import json
import shutil
import unittest

from application.court_profile_manager import CourtProfileManager, atomic_json_dump


class TestCourtProfileManager(unittest.TestCase):

    def setUp(self):
        self.test_root = "scratch/test_profiles_env"
        if os.path.exists(self.test_root):
            shutil.rmtree(self.test_root)
        os.makedirs(self.test_root, exist_ok=True)
        self.mgr = CourtProfileManager(root_dir=self.test_root)

    def tearDown(self):
        if os.path.exists(self.test_root):
            try:
                shutil.rmtree(self.test_root)
            except Exception:
                pass

    def test_01_default_migration_and_bootstrap(self):
        """Test automatic creation of Court 1 default profile on missing profiles.json."""
        registry = self.mgr.load_registry()
        self.assertEqual(registry.get("active_profile"), "court_1")

        profiles = self.mgr.list_profiles()
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0]["id"], "court_1")

        p_data, c_path, a_path = self.mgr.load_profile("court_1")
        self.assertEqual(p_data["name"], "Court 1")
        self.assertTrue(os.path.exists(c_path))
        self.assertTrue(os.path.exists(a_path))

    def test_02_create_and_load_profile(self):
        """Test creating a new profile and loading its configuration."""
        p_id = self.mgr.create_profile(
            profile_id="court_2",
            name="Court 2",
            description="Secondary Court",
            settings_dict={"quality": "performance", "racket_protection": False}
        )
        self.assertEqual(p_id, "court_2")

        p_data, c_path, a_path = self.mgr.load_profile("court_2")
        self.assertEqual(p_data["name"], "Court 2")
        self.assertEqual(p_data["settings"]["quality"], "performance")
        self.assertFalse(p_data["settings"]["racket_protection"])
        self.assertTrue(os.path.exists(c_path))
        self.assertTrue(os.path.exists(a_path))

    def test_03_duplicate_rejection(self):
        """Verify that duplicate profile IDs and duplicate profile names are rejected."""
        self.mgr.create_profile(profile_id="court_2", name="Court 2")

        with self.assertRaises(ValueError):
            self.mgr.create_profile(profile_id="court_2", name="Court 2 Duplicate ID")

        with self.assertRaises(ValueError):
            self.mgr.create_profile(profile_id="court_3", name="Court 2")

    def test_04_profile_isolation(self):
        """
        MANDATORY FEATURE 30: Profile Isolation Test.
        Modify Court 1 calibration/ads and verify Court 2 remains unchanged.
        Modify Court 2 calibration/ads and verify Court 1 remains unchanged.
        """
        self.mgr.create_profile(profile_id="court_2", name="Court 2")

        _, c1_path, a1_path = self.mgr.load_profile("court_1")
        _, c2_path, a2_path = self.mgr.load_profile("court_2")

        # Read initial state
        with open(c1_path, "r") as f:
            c1_orig = json.load(f)
        with open(c2_path, "r") as f:
            c2_orig = json.load(f)

        # 1. Modify Court 1 calibration & ads
        c1_modified = dict(c1_orig)
        c1_modified["court_points"] = [[100, 100], [200, 100], [200, 200], [100, 200]]
        atomic_json_dump(c1_modified, c1_path)

        a1_modified = {"ads": [{"name": "court1_exclusive_ad", "image": "ads/ad1.png"}]}
        atomic_json_dump(a1_modified, a1_path)

        # Verify Court 2 is COMPLETELY UNTOUCHED
        with open(c2_path, "r") as f:
            c2_curr = json.load(f)
        with open(a2_path, "r") as f:
            a2_curr = json.load(f)

        self.assertEqual(c2_curr, c2_orig)
        self.assertNotEqual(c2_curr, c1_modified)
        self.assertNotIn("court1_exclusive_ad", [a.get("name") for a in a2_curr.get("ads", [])])

        # 2. Modify Court 2 calibration & ads
        c2_modified = dict(c2_orig)
        c2_modified["court_points"] = [[999, 999], [888, 999], [888, 888], [999, 888]]
        atomic_json_dump(c2_modified, c2_path)

        a2_modified = {"ads": [{"name": "court2_exclusive_ad", "image": "ads/ad2.png"}]}
        atomic_json_dump(a2_modified, a2_path)

        # Verify Court 1 remains strictly isolated
        with open(c1_path, "r") as f:
            c1_curr = json.load(f)
        with open(a1_path, "r") as f:
            a1_curr = json.load(f)

        self.assertEqual(c1_curr, c1_modified)
        self.assertNotEqual(c1_curr, c2_modified)

    def test_05_update_and_rename_profile(self):
        """Test updating profile metadata and settings."""
        self.mgr.create_profile(profile_id="court_2", name="Court 2")
        updated = self.mgr.update_profile(
            profile_id="court_2",
            name="Court Center 2",
            description="Updated Description",
            settings_dict={"quality": "performance", "racket_protection": True}
        )
        self.assertEqual(updated["name"], "Court Center 2")

        profiles = self.mgr.list_profiles()
        p_names = [p["name"] for p in profiles]
        self.assertIn("Court Center 2", p_names)

    def test_06_delete_profile(self):
        """Test deleting a profile safely."""
        self.mgr.create_profile(profile_id="court_2", name="Court 2")
        self.assertEqual(len(self.mgr.list_profiles()), 2)

        self.mgr.set_active_profile_id("court_2")
        new_active = self.mgr.delete_profile("court_2")

        self.assertEqual(len(self.mgr.list_profiles()), 1)
        self.assertEqual(new_active, "court_1")
        self.assertFalse(os.path.exists(self.mgr.get_profile_dir("court_2")))

    def test_07_cannot_delete_last_profile(self):
        """Verify that deleting the only remaining court profile raises ValueError."""
        with self.assertRaises(ValueError):
            self.mgr.delete_profile("court_1")

    def test_08_atomic_save(self):
        """Test atomic file writing helper."""
        test_file = os.path.join(self.test_root, "atomic_test.json")
        data = {"key": "atomic_value_123"}
        atomic_json_dump(data, test_file)

        self.assertTrue(os.path.exists(test_file))
        with open(test_file, "r") as f:
            read_back = json.load(f)
        self.assertEqual(read_back, data)


if __name__ == "__main__":
    unittest.main()

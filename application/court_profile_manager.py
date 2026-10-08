"""
Court Profile Manager for CourtVision.
Handles creation, persistence, discovery, validation, activation, and isolation
of multi-court profiles (Court 1, Court 2, etc.) without duplicating CV engine components.
"""
import os
import sys
import json
import shutil
import time
import re


def atomic_json_dump(data, file_path):
    """Safely write JSON data to file using atomic temporary file replacement."""
    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    temp_path = f"{file_path}.tmp_{os.getpid()}_{time.time_ns()}"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_path, file_path)


class CourtProfileManager:
    """
    Manages multi-court profiles independently:
    Each profile stores court.json, ads.json, camera setup, and quality settings.
    """

    def __init__(self, root_dir="."):
        self.root_dir = root_dir
        self.config_dir = os.path.join(self.root_dir, "config")
        self.registry_path = os.path.join(self.config_dir, "profiles.json")
        self.profiles_dir = os.path.join(self.config_dir, "profiles")

        self._ensure_default_profile()

    def _ensure_default_profile(self):
        """
        Bootstrap migration: If profiles system does not exist, automatically
        migrate existing root config/court.json and config/ads.json into Court 1 (court_1).
        """
        os.makedirs(self.profiles_dir, exist_ok=True)

        if not os.path.exists(self.registry_path):
            court_1_dir = os.path.join(self.profiles_dir, "court_1")
            os.makedirs(court_1_dir, exist_ok=True)

            # Copy existing court.json or write standard default
            root_court = os.path.join(self.config_dir, "court.json")
            target_court = os.path.join(court_1_dir, "court.json")
            if os.path.exists(root_court):
                shutil.copy2(root_court, target_court)
            else:
                default_court = {
                    "court_points": [[517.8, 369.3], [770.6, 365.1], [1168.8, 587.3], [92.3, 590.5]],
                    "frame_size": [1280, 720],
                    "court_size_m": [10.97, 23.77],
                    "point_order": "far-left, far-right, near-right, near-left"
                }
                atomic_json_dump(default_court, target_court)

            # Copy existing ads.json or write standard default
            root_ads = os.path.join(self.config_dir, "ads.json")
            target_ads = os.path.join(court_1_dir, "ads.json")
            if os.path.exists(root_ads):
                shutil.copy2(root_ads, target_ads)
            else:
                default_ads = {
                    "ads": [
                        {
                            "name": "left_baseline",
                            "image": "ads/ad1.png",
                            "x0": 1.2,
                            "y0": 14.5,
                            "x1": 4.4,
                            "y1": 21.0,
                            "opacity": 1.0
                        },
                        {
                            "name": "right_baseline",
                            "image": "ads/ad2.png",
                            "x0": 6.57,
                            "y0": 14.5,
                            "x1": 9.77,
                            "y1": 21.0,
                            "opacity": 1.0
                        }
                    ]
                }
                atomic_json_dump(default_ads, target_ads)

            # Write court_1 profile.json
            profile_data = {
                "id": "court_1",
                "name": "Court 1",
                "description": "Main Court",
                "court_config": "court.json",
                "ads_config": "ads.json",
                "camera": {
                    "name": "Camera 0",
                    "type": "webcam",
                    "source": 0,
                    "reconnect": True,
                    "reconnect_delay": 3.0
                },
                "settings": {
                    "quality": "production",
                    "racket_protection": True,
                    "recording_enabled": False
                }
            }
            atomic_json_dump(profile_data, os.path.join(court_1_dir, "profile.json"))

            # Create profiles.json registry
            registry_data = {
                "active_profile": "court_1",
                "profiles": [
                    {
                        "id": "court_1",
                        "name": "Court 1",
                        "path": "config/profiles/court_1"
                    }
                ]
            }
            atomic_json_dump(registry_data, self.registry_path)

    def load_registry(self):
        """Load profile registry dictionary."""
        if not os.path.exists(self.registry_path):
            self._ensure_default_profile()

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[CourtProfileManager] Error loading registry: {e}. Rebuilding default registry.")
            self._ensure_default_profile()
            with open(self.registry_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def list_profiles(self):
        """Return list of available profile dictionaries."""
        registry = self.load_registry()
        return registry.get("profiles", [])

    def get_active_profile_id(self):
        """Return active profile ID."""
        registry = self.load_registry()
        active = registry.get("active_profile", "court_1")
        # Verify active profile directory exists
        profiles = registry.get("profiles", [])
        valid_ids = [p["id"] for p in profiles]
        if active not in valid_ids and valid_ids:
            active = valid_ids[0]
            self.set_active_profile_id(active)
        return active

    def set_active_profile_id(self, profile_id):
        """Set active profile ID in registry."""
        registry = self.load_registry()
        profiles = registry.get("profiles", [])
        valid_ids = [p["id"] for p in profiles]
        if profile_id not in valid_ids:
            raise ValueError(f"Profile ID '{profile_id}' does not exist in registry.")

        registry["active_profile"] = profile_id
        atomic_json_dump(registry, self.registry_path)
        return True

    def get_profile_dir(self, profile_id):
        """Return directory path for given profile ID."""
        return os.path.join(self.profiles_dir, profile_id)

    def load_profile(self, profile_id):
        """
        Load complete configuration for a profile.
        Returns (profile_data, court_config_path, ads_config_path).
        """
        p_dir = self.get_profile_dir(profile_id)
        p_json_path = os.path.join(p_dir, "profile.json")

        if not os.path.exists(p_json_path):
            raise FileNotFoundError(f"Profile configuration missing: {p_json_path}")

        with open(p_json_path, "r", encoding="utf-8") as f:
            profile_data = json.load(f)

        court_config_path = os.path.join(p_dir, profile_data.get("court_config", "court.json"))
        ads_config_path = os.path.join(p_dir, profile_data.get("ads_config", "ads.json"))

        if not os.path.exists(court_config_path):
            # Create default court.json if missing
            default_court = {
                "court_points": [[517.8, 369.3], [770.6, 365.1], [1168.8, 587.3], [92.3, 590.5]],
                "frame_size": [1280, 720],
                "court_size_m": [10.97, 23.77],
                "point_order": "far-left, far-right, near-right, near-left"
            }
            atomic_json_dump(default_court, court_config_path)

        if not os.path.exists(ads_config_path):
            default_ads = {"ads": []}
            atomic_json_dump(default_ads, ads_config_path)

        return profile_data, court_config_path, ads_config_path

    def create_profile(self, profile_id, name, description="", camera_dict=None, settings_dict=None, copy_from_id=None):
        """
        Create a new court profile with isolated court.json and ads.json configurations.
        """
        # Sanitize profile_id
        profile_id = re.sub(r'[^a-zA-Z0-9_]', '_', profile_id.lower().strip())
        if not profile_id:
            raise ValueError("Profile ID must not be empty.")

        registry = self.load_registry()
        profiles = registry.get("profiles", [])

        # Check unique ID and Name
        for p in profiles:
            if p["id"] == profile_id:
                raise ValueError(f"Profile ID '{profile_id}' already exists.")
            if p["name"].lower() == name.lower():
                raise ValueError(f"Profile name '{name}' already exists.")

        p_dir = os.path.join(self.profiles_dir, profile_id)
        os.makedirs(p_dir, exist_ok=True)

        court_path = os.path.join(p_dir, "court.json")
        ads_path = os.path.join(p_dir, "ads.json")

        if copy_from_id:
            src_dir = self.get_profile_dir(copy_from_id)
            if os.path.exists(os.path.join(src_dir, "court.json")):
                shutil.copy2(os.path.join(src_dir, "court.json"), court_path)
            if os.path.exists(os.path.join(src_dir, "ads.json")):
                shutil.copy2(os.path.join(src_dir, "ads.json"), ads_path)

        if not os.path.exists(court_path):
            default_court = {
                "court_points": [[517.8, 369.3], [770.6, 365.1], [1168.8, 587.3], [92.3, 590.5]],
                "frame_size": [1280, 720],
                "court_size_m": [10.97, 23.77],
                "point_order": "far-left, far-right, near-right, near-left"
            }
            atomic_json_dump(default_court, court_path)

        if not os.path.exists(ads_path):
            default_ads = {
                "ads": [
                    {
                        "name": "left_baseline",
                        "image": "ads/ad1.png",
                        "x0": 1.2,
                        "y0": 14.5,
                        "x1": 4.4,
                        "y1": 21.0,
                        "opacity": 1.0
                    }
                ]
            }
            atomic_json_dump(default_ads, ads_path)

        profile_data = {
            "id": profile_id,
            "name": name,
            "description": description,
            "court_config": "court.json",
            "ads_config": "ads.json",
            "camera": camera_dict or {
                "name": f"Camera ({name})",
                "type": "webcam",
                "source": 0,
                "reconnect": True,
                "reconnect_delay": 3.0
            },
            "settings": settings_dict or {
                "quality": "production",
                "racket_protection": True,
                "recording_enabled": False
            }
        }

        atomic_json_dump(profile_data, os.path.join(p_dir, "profile.json"))

        # Update registry
        profiles.append({
            "id": profile_id,
            "name": name,
            "path": f"config/profiles/{profile_id}"
        })
        registry["profiles"] = profiles
        atomic_json_dump(registry, self.registry_path)

        return profile_id

    def update_profile(self, profile_id, name=None, description=None, camera_dict=None, settings_dict=None):
        """Update profile metadata and configuration settings atomically."""
        p_dir = self.get_profile_dir(profile_id)
        p_json_path = os.path.join(p_dir, "profile.json")

        if not os.path.exists(p_json_path):
            raise FileNotFoundError(f"Profile {profile_id} does not exist.")

        with open(p_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if name and name != data.get("name"):
            # Verify name uniqueness
            registry = self.load_registry()
            for p in registry.get("profiles", []):
                if p["id"] != profile_id and p["name"].lower() == name.lower():
                    raise ValueError(f"Profile name '{name}' already exists.")
            data["name"] = name

            # Update in registry
            for p in registry.get("profiles", []):
                if p["id"] == profile_id:
                    p["name"] = name
            atomic_json_dump(registry, self.registry_path)

        if description is not None:
            data["description"] = description
        if camera_dict is not None:
            data["camera"] = camera_dict
        if settings_dict is not None:
            data["settings"] = settings_dict

        atomic_json_dump(data, p_json_path)
        return data

    def delete_profile(self, profile_id):
        """Delete a profile safely. Cannot delete active profile if it's the only one."""
        registry = self.load_registry()
        profiles = registry.get("profiles", [])

        if len(profiles) <= 1:
            raise ValueError("Cannot delete the only remaining court profile.")

        valid_ids = [p["id"] for p in profiles]
        if profile_id not in valid_ids:
            raise ValueError(f"Profile '{profile_id}' does not exist.")

        # Remove from registry
        new_profiles = [p for p in profiles if p["id"] != profile_id]
        registry["profiles"] = new_profiles

        if registry.get("active_profile") == profile_id:
            registry["active_profile"] = new_profiles[0]["id"]

        atomic_json_dump(registry, self.registry_path)

        # Delete profile folder
        p_dir = self.get_profile_dir(profile_id)
        if os.path.exists(p_dir):
            try:
                shutil.rmtree(p_dir)
            except Exception as e:
                print(f"[CourtProfileManager] Warning deleting directory {p_dir}: {e}")

        return registry["active_profile"]

    def validate_profile(self, profile_id):
        """Validate profile JSON files. Returns (is_valid, list_of_errors)."""
        errors = []
        p_dir = self.get_profile_dir(profile_id)

        if not os.path.exists(p_dir):
            return False, [f"Profile directory {p_dir} does not exist."]

        p_json = os.path.join(p_dir, "profile.json")
        if not os.path.exists(p_json):
            errors.append(f"Missing profile.json in {p_dir}")
        else:
            try:
                with open(p_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not data.get("name"):
                    errors.append("Profile missing 'name' field.")
            except Exception as e:
                errors.append(f"Malformed profile.json: {e}")

        court_json = os.path.join(p_dir, "court.json")
        if not os.path.exists(court_json):
            errors.append(f"Missing court.json in {p_dir}")
        else:
            try:
                with open(court_json, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                if "court_points" not in cdata:
                    errors.append("court.json missing 'court_points'")
            except Exception as e:
                errors.append(f"Malformed court.json: {e}")

        ads_json = os.path.join(p_dir, "ads.json")
        if not os.path.exists(ads_json):
            errors.append(f"Missing ads.json in {p_dir}")
        else:
            try:
                with open(ads_json, "r", encoding="utf-8") as f:
                    adata = json.load(f)
                if "ads" not in adata:
                    errors.append("ads.json missing 'ads' array")
            except Exception as e:
                errors.append(f"Malformed ads.json: {e}")

        return len(errors) == 0, errors

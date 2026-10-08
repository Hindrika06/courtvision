"""
Session Manager for CourtVision.
Persists application session state (active court, last quality, last source type)
to config/session.json using atomic file operations.
"""
import os
import sys
import json
from application.court_profile_manager import atomic_json_dump


class SessionManager:
    """
    Manages CourtVision operator session state persistence.
    """

    def __init__(self, session_path="config/session.json"):
        self.session_path = session_path

    def load_session(self):
        """
        Load session state from config/session.json.
        Returns fallback defaults if file is missing or invalid.
        """
        defaults = {
            "active_profile": "court_1",
            "last_quality": "production",
            "last_source_type": "webcam",
            "racket_protection": True
        }

        if not os.path.exists(self.session_path):
            return defaults

        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Ensure required keys exist
            defaults.update(data)
            return defaults
        except Exception as e:
            print(f"[SessionManager] Warning reading session file: {e}. Using defaults.")
            return defaults

    def save_session(self, active_profile="court_1", last_quality="production", last_source_type="webcam", racket_protection=True, extra_data=None):
        """
        Save session state atomically to config/session.json.
        Avoids writing sensitive data.
        """
        data = {
            "active_profile": str(active_profile),
            "last_quality": str(last_quality),
            "last_source_type": str(last_source_type),
            "racket_protection": bool(racket_protection)
        }

        if extra_data and isinstance(extra_data, dict):
            for k, v in extra_data.items():
                if k not in ("password", "secret", "credentials"):
                    data[k] = v

        try:
            atomic_json_dump(data, self.session_path)
            return True
        except Exception as e:
            print(f"[SessionManager] Error saving session file: {e}")
            return False

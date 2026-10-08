"""
CourtVision Version Information.
Centralized application metadata for CourtVision.
"""

APP_NAME = "CourtVision"
VERSION = "1.0.0"
BUILD_DATE = "2026-10-07"
AUTHOR = "CourtVision Engineering Team"
DESCRIPTION = "Real-Time Virtual Court Advertising Engine & Desktop Control Center"
AI_ENGINE = "YOLOv8 Segmentation & 3x3 Court Homography"


def get_version_string():
    """Return formatted version string."""
    return f"{APP_NAME} v{VERSION}"

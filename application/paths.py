"""
Centralized Path & Resource Resolution Helper for CourtVision.
Handles seamless path resolution across Python source execution and PyInstaller frozen executables.
Separates immutable application resources from writable user data (config, ads, output, logs).
"""
import os
import sys


def is_frozen():
    """Check if running inside a PyInstaller frozen executable."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_project_root():
    """
    Return base project directory.
    If frozen, returns directory containing executable; otherwise returns project source root.
    """
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # Current file is in application/paths.py, project root is parent directory
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_user_data_dir():
    """
    Return root directory for writable user data (config, profiles, ads, output, logs).
    Supports installation in Program Files by utilizing LocalAppData if needed.
    """
    root = get_project_root()
    # Check if program files (read-only)
    is_program_files = "program files" in root.lower() or "program files (x86)" in root.lower()

    if is_frozen() and is_program_files:
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        user_dir = os.path.join(local_app_data, "CourtVision")
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    else:
        return root


def get_resource_path(relative_path):
    """Get absolute path to bundled resource file."""
    if is_frozen():
        meipass_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(meipass_path):
            return meipass_path
        exe_path = os.path.join(get_project_root(), relative_path)
        if os.path.exists(exe_path):
            return exe_path
        return meipass_path
    else:
        return os.path.join(get_project_root(), relative_path)


def get_model_path(model_name="yolov8n-seg.pt"):
    """Locate AI segmentation model file."""
    # 1. Check user data models/
    user_model = os.path.join(get_user_data_dir(), "models", model_name)
    if os.path.exists(user_model):
        return user_model

    # 2. Check executable directory models/
    exe_model = os.path.join(get_project_root(), "models", model_name)
    if os.path.exists(exe_model):
        return exe_model

    # 3. Check PyInstaller _MEIPASS bundle
    if is_frozen():
        meipass_model = os.path.join(sys._MEIPASS, "models", model_name)
        if os.path.exists(meipass_model):
            return meipass_model

    # 4. Check project root models/
    root_model = os.path.join(get_project_root(), "models", model_name)

    return user_model if not os.path.exists(root_model) else root_model


def get_config_dir():
    """Return writable config directory."""
    d = os.path.join(get_user_data_dir(), "config")
    os.makedirs(d, exist_ok=True)
    return d


def get_ads_dir():
    """Return writable ads directory."""
    d = os.path.join(get_user_data_dir(), "ads")
    os.makedirs(d, exist_ok=True)
    return d


def get_output_dir():
    """Return writable output directory."""
    d = os.path.join(get_user_data_dir(), "output")
    os.makedirs(d, exist_ok=True)
    return d


def get_logs_dir():
    """Return writable logs directory."""
    d = os.path.join(get_user_data_dir(), "logs")
    os.makedirs(d, exist_ok=True)
    return d

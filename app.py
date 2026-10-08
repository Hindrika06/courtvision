"""
CourtVision Desktop Control Center Application Launcher.
Handles production startup initialization, model verification, logging,
and top-level exception handling for standalone executable and Python execution.

Usage:
    python app.py
    CourtVision.exe [--debug]
"""
import os
import sys
import traceback
import tkinter as tk
from tkinter import messagebox

from application.paths import get_model_path, get_logs_dir, get_user_data_dir
from application.version import get_version_string, VERSION, APP_NAME
from application.logger import setup_logger, log_info, log_error


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Global unhandled exception handler logging stack trace and showing user alert."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_error(f"Uncaught exception: {exc_value}\n{err_msg}", exc_info=True)

    # Show operator-friendly error popup
    try:
        root = tk.Tk()
        root.withdraw()
        log_file = os.path.join(get_logs_dir(), "courtvision.log")
        messagebox.showerror(
            f"{APP_NAME} Unexpected Error",
            f"An unexpected error occurred in {get_version_string()}.\n\n"
            f"Error: {exc_value}\n\n"
            f"Technical details have been logged to:\n{log_file}"
        )
        root.destroy()
    except Exception:
        pass


def validate_startup_environment():
    """Verify required AI models and writable runtime directories on startup."""
    log_info(f"Validating startup environment...")
    log_info(f"User Data Directory: {get_user_data_dir()}")

    # 1. Verify YOLO segmentation model file exists and is readable
    model_path = get_model_path("yolov8n-seg.pt")
    log_info(f"AI Model path: {model_path}")

    if not os.path.exists(model_path) or os.path.getsize(model_path) < 1000:
        err = f"Required AI model 'yolov8n-seg.pt' is missing or unreadable at: {model_path}"
        log_error(err)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Missing AI Model",
            f"{err}\n\nPlease place 'yolov8n-seg.pt' inside the models/ directory before launching CourtVision."
        )
        root.destroy()
        sys.exit(1)

    return True


def main():
    # Install top-level exception handler
    sys.excepthook = handle_uncaught_exception

    # Initialize production logger
    setup_logger()
    log_info(f"Launching {get_version_string()}...")

    # Validate environment & model assets
    validate_startup_environment()

    # Launch GUI
    root = tk.Tk()

    # Configure Tkinter exception callback handler
    def tkinter_exception_handler(exc_type, exc_value, exc_traceback):
        handle_uncaught_exception(exc_type, exc_value, exc_traceback)

    root.report_callback_exception = tkinter_exception_handler

    from ui.main_window import CourtVisionMainWindow
    app = CourtVisionMainWindow(root)
    root.mainloop()

    log_info(f"{get_version_string()} exited cleanly.")


if __name__ == "__main__":
    main()

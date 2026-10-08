"""
Interactive Court Calibration Wizard for CourtVision Desktop Application.
Reuses calibration mathematics from vision/calibration.py without code duplication.
"""
import os
import json
import cv2
import numpy as np

from vision.calibration import (
    load_calibration, save_calibration, is_valid_quad, render, PAD, LABELS
)


class CalibrationWizard:
    """
    OpenCV / Tkinter / PySide6 GUI bridge for interactive court calibration.
    """

    def __init__(self, source, config_path="config/court.json"):
        self.source = source
        self.config_path = config_path

    def run(self):
        """
        Launch interactive calibration window.
        Returns True if successfully saved, False otherwise.
        """
        parsed_source = int(self.source) if isinstance(self.source, str) and self.source.isdigit() else self.source
        cap = cv2.VideoCapture(parsed_source)
        if not cap.isOpened():
            print(f"[CalibrationWizard] Error: Could not open source: {self.source}")
            return False

        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            print("[CalibrationWizard] Error: Could not read frame from source.")
            return False

        h, w = frame.shape[:2]
        scale = min(1.0, 1400.0 / (w + 2 * PAD))

        points = []
        old = load_calibration(self.config_path)
        if old and old.get("frame_size") == [w, h]:
            points = [list(p) for p in old["court_points"]]

        state = {"drag": None, "saved": False}

        def to_image(x, y):
            return x / scale - PAD, y / scale - PAD

        def on_mouse(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                for i, (px, py) in enumerate(points):
                    dx = (px + PAD) * scale - x
                    dy = (py + PAD) * scale - y
                    if dx * dx + dy * dy < 15 * 15:
                        state["drag"] = i
                        return
                if len(points) < 4:
                    ix, iy = to_image(x, y)
                    points.append([ix, iy])
            elif event == cv2.EVENT_MOUSEMOVE and state["drag"] is not None:
                ix, iy = to_image(x, y)
                points[state["drag"]] = [ix, iy]
            elif event == cv2.EVENT_LBUTTONUP:
                state["drag"] = None

        win = "CourtVision Calibration Wizard"
        cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(win, on_mouse)

        while True:
            if len(points) < 4:
                status = f"Click point {len(points) + 1}/4: {LABELS[len(points)]}   (U=undo R=reset Q=quit)"
            elif not is_valid_quad(points):
                status = "Points are in wrong order! Press R and redo: (1 far-left, 2 far-right, 3 near-right, 4 near-left)"
            else:
                status = "Drag points to fine-tune. Press S to SAVE calibration to config/court.json"

            cv2.imshow(win, render(frame, points, scale, status))
            key = cv2.waitKey(30) & 0xFF

            if key in (ord("q"), ord("Q"), 27):
                break
            elif key in (ord("r"), ord("R")):
                points.clear()
            elif key in (ord("u"), ord("U")) and points:
                points.pop()
            elif key in (ord("s"), ord("S")):
                if is_valid_quad(points):
                    save_calibration(self.config_path, points, (w, h))
                    print(f"[CalibrationWizard] Calibration saved to {self.config_path}")
                    state["saved"] = True
                    break
                else:
                    print("[CalibrationWizard] Error: 4 valid convex points required.")

        cv2.destroyWindow(win)
        return state["saved"]

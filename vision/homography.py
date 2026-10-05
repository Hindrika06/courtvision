"""
Homography helpers.
Court coordinates are in metres:
    x: 0 (left sideline)  -> 10.97 (right sideline)
    y: 0 (far baseline)   -> 23.77 (near baseline), net at 11.885
"""
import json

import cv2
import numpy as np

COURT_W = 10.97
COURT_L = 23.77


def load_court(path="config/court.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_homography(court_points):
    """Matrix that converts court metres -> image pixels."""
    model = np.float32([[0, 0], [COURT_W, 0], [COURT_W, COURT_L], [0, COURT_L]])
    return cv2.getPerspectiveTransform(model, np.float32(court_points))


def court_to_image(H, points_m):
    """Convert a list of (x, y) court points in metres into image pixels."""
    pts = np.float32(points_m).reshape(-1, 1, 2)
    return cv2.perspectiveTransform(pts, H).reshape(-1, 2)


def rect_to_quad(H, x0, y0, x1, y1):
    """A rectangle on the court (metres) -> 4 image corners (TL, TR, BR, BL)."""
    corners = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    return court_to_image(H, corners)

"""
Court calibration tool.

Run:  python -m vision.calibration
Click the 4 corners of the court (outer lines), in this order:
    1 far-left, 2 far-right, 3 near-right, 4 near-left
You can click in the gray margin if a corner is outside the picture.
"""
import argparse
import json
import os
import sys

# pyrefly: ignore [missing-import]
import cv2
import numpy as np

# Real tennis doubles court size in metres
COURT_W = 10.97
COURT_L = 23.77
NET_Y = COURT_L / 2
SERVICE_Y1 = NET_Y - 6.40   # far service line
SERVICE_Y2 = NET_Y + 6.40   # near service line
SINGLES_INSET = (10.97 - 8.23) / 2

PAD = 150  # gray margin (pixels) around the frame
LABELS = ["1 far-left", "2 far-right", "3 near-right", "4 near-left"]


def court_model_points():
    """The court as a perfect rectangle in metres (far-left, far-right, near-right, near-left)."""
    return np.float32([[0, 0], [COURT_W, 0], [COURT_W, COURT_L], [0, COURT_L]])


def model_to_image_matrix(points):
    """Homography: court metres -> image pixels."""
    return cv2.getPerspectiveTransform(court_model_points(), np.float32(points))


def save_calibration(path, points, frame_size):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = {
        "court_points": [[round(float(x), 1), round(float(y), 1)] for x, y in points],
        "frame_size": [int(frame_size[0]), int(frame_size[1])],
        "court_size_m": [COURT_W, COURT_L],
        "point_order": "far-left, far-right, near-right, near-left",
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_calibration(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_valid_quad(points):
    return len(points) == 4 and cv2.isContourConvex(np.int32(points).reshape(-1, 1, 2))


def render(frame, points, scale, status):
    canvas = cv2.copyMakeBorder(frame, PAD, PAD, PAD, PAD,
                                cv2.BORDER_CONSTANT, value=(70, 70, 70))
    pts_c = [(int(x + PAD), int(y + PAD)) for x, y in points]

    if len(points) == 4:
        color = (0, 255, 0) if is_valid_quad(points) else (0, 0, 255)
        cv2.polylines(canvas, [np.int32(pts_c)], True, color, 2)

        H = model_to_image_matrix(points)
        segments = [
            ((0, NET_Y), (COURT_W, NET_Y), (0, 0, 255)),                      # net (red)
            ((0, SERVICE_Y1), (COURT_W, SERVICE_Y1), (0, 255, 255)),          # service lines
            ((0, SERVICE_Y2), (COURT_W, SERVICE_Y2), (0, 255, 255)),
            ((COURT_W / 2, SERVICE_Y1), (COURT_W / 2, SERVICE_Y2), (0, 255, 255)),
            ((SINGLES_INSET, 0), (SINGLES_INSET, COURT_L), (0, 255, 255)),    # singles lines
            ((COURT_W - SINGLES_INSET, 0), (COURT_W - SINGLES_INSET, COURT_L), (0, 255, 255)),
        ]
        for a, b, col in segments:
            p = cv2.perspectiveTransform(np.float32([[a, b]]), H)[0]
            pa = (int(p[0][0] + PAD), int(p[0][1] + PAD))
            pb = (int(p[1][0] + PAD), int(p[1][1] + PAD))
            cv2.line(canvas, pa, pb, col, 1, cv2.LINE_AA)

    for i, c in enumerate(pts_c):
        cv2.circle(canvas, c, 5, (0, 0, 255), -1)
        cv2.putText(canvas, LABELS[i], (c[0] + 8, c[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    if scale != 1.0:
        canvas = cv2.resize(canvas, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    cv2.putText(canvas, status, (10, canvas.shape[0] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    return canvas


def run_calibration(source, config_path, frame_index=0):
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"ERROR: could not open {source}")
        return False
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        print("ERROR: could not read a frame")
        return False

    h, w = frame.shape[:2]
    scale = min(1.0, 1500.0 / (w + 2 * PAD))

    points = []
    old = load_calibration(config_path)
    if old and old.get("frame_size") == [w, h]:
        points = [list(p) for p in old["court_points"]]
        print("Loaded existing calibration. Drag points to adjust.")
    elif old:
        print("WARNING: saved calibration is for a different video size. Starting fresh.")

    state = {"drag": None, "saved": False}

    def to_image(x, y):
        return x / scale - PAD, y / scale - PAD

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # near an existing point? start dragging it
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

    win = "Calibration"
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(win, on_mouse)

    while True:
        if len(points) < 4:
            status = f"Click point {len(points) + 1}/4: {LABELS[len(points)]}   (U=undo R=reset Q=quit)"
        elif not is_valid_quad(points):
            status = "Points are in the wrong order! Press R and redo. (far-left, far-right, near-right, near-left)"
        else:
            status = "Drag points to fine-tune.  S=save  R=reset  U=undo  Q=quit"

        cv2.imshow(win, render(frame, points, scale, status))
        key = cv2.waitKey(30) & 0xFF

        if key in (ord("q"), 27):
            break
        elif key == ord("r"):
            points.clear()
        elif key == ord("u") and points:
            points.pop()
        elif key == ord("s"):
            if is_valid_quad(points):
                save_calibration(config_path, points, (w, h))
                print(f"Saved calibration to {config_path}")
                print(json.dumps(load_calibration(config_path), indent=4))
                state["saved"] = True
                break
            else:
                print("Need 4 valid points in the right order before saving.")

    cv2.destroyAllWindows()
    return state["saved"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="input/input.mp4")
    parser.add_argument("--config", default="config/court.json")
    parser.add_argument("--frame", type=int, default=0, help="which frame to calibrate on")
    args = parser.parse_args()
    sys.exit(0 if run_calibration(args.source, args.config, args.frame) else 1)
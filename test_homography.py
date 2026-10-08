import sys

# pyrefly: ignore [missing-import]
import cv2
import numpy as np

from vision.homography import (build_homography, court_to_image, load_court,
                               rect_to_quad, COURT_W, COURT_L)

VIDEO = "input/input.mp4"
NO_DISPLAY = False
for arg in sys.argv[1:]:
    if arg == "--no-display":
        NO_DISPLAY = True
    elif not arg.startswith("--"):
        VIDEO = arg

# Test rectangles in court metres: (name, x0, y0, x1, y1, BGR colour)
TEST_RECTS = [
    ("LEFT",   1.2, 14.5, 4.4, 21.0, (0, 0, 255)),
    ("RIGHT",  6.57, 14.5, 9.77, 21.0, (0, 255, 0)),
    ("CENTER", 2.8, 6.5, 8.2, 10.8, (255, 0, 0)),
]
cap = cv2.VideoCapture(VIDEO)
if not cap.isOpened():
    sys.exit(f"ERROR: could not open {VIDEO}")

w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

try:
    court = load_court("config/court.json")
except FileNotFoundError:
    sys.exit("ERROR: config/court.json not found. Run: python -m vision.calibration")

if court["frame_size"] != [w, h]:
    sys.exit(f"ERROR: calibration is for {court['frame_size']} but video is {[w, h]}. Recalibrate.")

H = build_homography(court["court_points"])
quads = [(name, rect_to_quad(H, x0, y0, x1, y1), col)
         for name, x0, y0, x1, y1, col in TEST_RECTS]
outline = court_to_image(H, [[0, 0], [COURT_W, 0], [COURT_W, COURT_L], [0, COURT_L]])


def draw(frame):
    overlay = frame.copy()
    for name, q, col in quads:
        cv2.fillPoly(overlay, [np.int32(q)], col)
    out = cv2.addWeighted(overlay, 0.4, frame, 0.6, 0)
    for name, q, col in quads:
        cv2.polylines(out, [np.int32(q)], True, col, 2, cv2.LINE_AA)
        cx, cy = np.int32(q.mean(axis=0))
        cv2.putText(out, name, (cx - 25, cy), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.polylines(out, [np.int32(outline)], True, (255, 255, 255), 1, cv2.LINE_AA)
    return out


ok, frame = cap.read()
cv2.imwrite("output/step3_test.jpg", draw(frame))
print("Saved output/step3_test.jpg")

if not NO_DISPLAY:
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    while True:
        ok, frame = cap.read()
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # loop the video
            continue
        cv2.imshow("Step 3 - test rectangles (q to quit)", draw(frame))
        if cv2.waitKey(33) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
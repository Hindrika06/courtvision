import sys
# pyrefly: ignore [missing-import]
import cv2

# Video path: use the first argument if given, otherwise the default
path = sys.argv[1] if len(sys.argv) > 1 else "input/input.mp4"

cap = cv2.VideoCapture(path)
if not cap.isOpened():
    print(f"ERROR: could not open video: {path}")
    sys.exit(1)

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print(f"Video     : {path}")
print(f"Size      : {width} x {height}")
print(f"FPS       : {fps:.2f}")
print(f"Frames    : {count}  (about {count / fps:.1f} seconds)")

ok, frame = cap.read()
if not ok:
    print("ERROR: could not read the first frame")
    sys.exit(1)

# Save the first frame (we will click calibration points on it later)
cv2.imwrite("output/first_frame.jpg", frame)
print("Saved first frame to output/first_frame.jpg")

# Show the first frame. Press any key to continue, then play the video.
view = frame
if width > 1280:
    scale = 1280 / width
    view = cv2.resize(frame, None, fx=scale, fy=scale)
cv2.imshow("First frame - press any key", view)
cv2.waitKey(0)

# Play the video. Press q to quit.
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
delay = int(1000 / fps) if fps > 0 else 33
while True:
    ok, frame = cap.read()
    if not ok:
        break
    if width > 1280:
        frame = cv2.resize(frame, None, fx=scale, fy=scale)
    cv2.imshow("Playback - press q to quit", frame)
    if cv2.waitKey(delay) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("Done.")
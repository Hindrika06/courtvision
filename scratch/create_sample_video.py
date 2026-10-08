import os
import cv2
import numpy as np
from vision.homography import build_homography, court_to_image, COURT_W, COURT_L

def create_synthetic_video(output_path="input/input.mp4", width=1280, height=720, fps=30, duration_sec=5):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define corners corresponding to config/court.json
    court_pts = np.float32([[517.8, 369.3], [770.6, 365.1], [1168.8, 587.3], [92.3, 590.5]])
    H = build_homography(court_pts)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Pre-calculate court line segments in image coordinates
    NET_Y = COURT_L / 2
    SERVICE_Y1 = NET_Y - 6.40
    SERVICE_Y2 = NET_Y + 6.40
    SINGLES_INSET = (10.97 - 8.23) / 2
    
    lines_m = [
        # Outer boundary
        [(0, 0), (COURT_W, 0)],
        [(COURT_W, 0), (COURT_W, COURT_L)],
        [(COURT_W, COURT_L), (0, COURT_L)],
        [(0, COURT_L), (0, 0)],
        # Net
        [(0, NET_Y), (COURT_W, NET_Y)],
        # Service lines
        [(0, SERVICE_Y1), (COURT_W, SERVICE_Y1)],
        [(0, SERVICE_Y2), (COURT_W, SERVICE_Y2)],
        [(COURT_W / 2, SERVICE_Y1), (COURT_W / 2, SERVICE_Y2)],
        # Singles lines
        [(SINGLES_INSET, 0), (SINGLES_INSET, COURT_L)],
        [(COURT_W - SINGLES_INSET, 0), (COURT_W - SINGLES_INSET, COURT_L)],
    ]
    
    lines_px = []
    for (p1, p2) in lines_m:
        pts = court_to_image(H, [p1, p2])
        lines_px.append((tuple(np.int32(pts[0])), tuple(np.int32(pts[1]))))
        
    poly_outer = np.int32(court_pts)
    
    total_frames = fps * duration_sec
    for frame_idx in range(total_frames):
        # Create court canvas (dark green background, blue/cyan court surface inside quad)
        frame = np.full((height, width, 3), (34, 110, 48), dtype=np.uint8) # Green surround
        
        # Fill court interior with hardcourt blue
        cv2.fillPoly(frame, [poly_outer], (140, 90, 40))
        
        # Draw white court lines
        for p1, p2 in lines_px:
            cv2.line(frame, p1, p2, (255, 255, 255), 3, cv2.LINE_AA)
            
        # Draw moving tennis ball
        t = frame_idx / total_frames
        ball_x = COURT_W / 2 + np.sin(t * 2 * np.pi * 2) * 3.5
        ball_y = COURT_L / 2 + np.cos(t * 2 * np.pi * 1.5) * 8.0
        ball_img_pt = court_to_image(H, [(ball_x, ball_y)])[0]
        bx, by = int(ball_img_pt[0]), int(ball_img_pt[1])
        cv2.circle(frame, (bx, by), 7, (0, 240, 255), -1, cv2.LINE_AA)
        
        out.write(frame)
        
    out.release()
    print(f"Successfully generated synthetic video at {output_path} ({width}x{height}, {fps} fps, {duration_sec}s)")

if __name__ == "__main__":
    create_synthetic_video()

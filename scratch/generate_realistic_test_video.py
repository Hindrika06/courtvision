"""
Generates a realistic test video input/test_players.mp4 with moving players walking/running over baseline virtual ads.
Used to validate Scenarios A through G and test mask occlusion.
"""
import os
import sys
sys.path.insert(0, ".")
import cv2
import numpy as np
from vision.homography import build_homography, court_to_image, COURT_W, COURT_L



def generate_test_players_video(output_path="input/test_players.mp4", width=1280, height=720, fps=30, duration_sec=8):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    court_pts = np.float32([[517.8, 369.3], [770.6, 365.1], [1168.8, 587.3], [92.3, 590.5]])
    H = build_homography(court_pts)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    NET_Y = COURT_L / 2
    SERVICE_Y1 = NET_Y - 6.40
    SERVICE_Y2 = NET_Y + 6.40
    SINGLES_INSET = (10.97 - 8.23) / 2
    
    lines_m = [
        [(0, 0), (COURT_W, 0)],
        [(COURT_W, 0), (COURT_W, COURT_L)],
        [(COURT_W, COURT_L), (0, COURT_L)],
        [(0, COURT_L), (0, 0)],
        [(0, NET_Y), (COURT_W, NET_Y)],
        [(0, SERVICE_Y1), (COURT_W, SERVICE_Y1)],
        [(0, SERVICE_Y2), (COURT_W, SERVICE_Y2)],
        [(COURT_W / 2, SERVICE_Y1), (COURT_W / 2, SERVICE_Y2)],
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
        t = frame_idx / total_frames
        
        # Court background
        frame = np.full((height, width, 3), (34, 110, 48), dtype=np.uint8)
        cv2.fillPoly(frame, [poly_outer], (140, 90, 40))
        
        for p1, p2 in lines_px:
            cv2.line(frame, p1, p2, (255, 255, 255), 3, cv2.LINE_AA)
            
        # Draw realistic player stick/body shapes moving across baseline ad (y=17.5m)
        # Player 1 (walks across left baseline ad x: 1.2 -> 4.4, y: 17.5)
        p1_x = 0.5 + t * 5.0
        p1_y = 17.5
        p1_img_pt = court_to_image(H, [(p1_x, p1_y)])[0]
        cx, cy = int(p1_img_pt[0]), int(p1_img_pt[1])
        
        # Head
        cv2.circle(frame, (cx, cy - 65), 14, (200, 160, 120), -1, cv2.LINE_AA)
        # Shirt / Body (Red shirt)
        cv2.rectangle(frame, (cx - 16, cy - 50), (cx + 16, cy - 10), (50, 50, 220), -1)
        # Legs (Shorts & legs)
        cv2.rectangle(frame, (cx - 12, cy - 10), (cx - 2, cy + 25), (220, 220, 220), -1)
        cv2.rectangle(frame, (cx + 2, cy - 10), (cx + 12, cy + 25), (220, 220, 220), -1)
        # Arms raised occasionally
        arm_angle = np.sin(t * 10 * np.pi) * 30
        cv2.line(frame, (cx - 16, cy - 45), (cx - 30, int(cy - 45 - arm_angle)), (200, 160, 120), 6, cv2.LINE_AA)
        cv2.line(frame, (cx + 16, cy - 45), (cx + 30, int(cy - 45 + arm_angle)), (200, 160, 120), 6, cv2.LINE_AA)
        
        # Player 2 (runs across right baseline ad x: 6.57 -> 9.77, y: 17.5)
        p2_x = 10.5 - t * 5.0
        p2_y = 17.5
        p2_img_pt = court_to_image(H, [(p2_x, p2_y)])[0]
        cx2, cy2 = int(p2_img_pt[0]), int(p2_img_pt[1])
        
        # Head
        cv2.circle(frame, (cx2, cy2 - 65), 14, (180, 150, 110), -1, cv2.LINE_AA)
        # Shirt / Body (Yellow shirt)
        cv2.rectangle(frame, (cx2 - 16, cy2 - 50), (cx2 + 16, cy2 - 10), (20, 220, 220), -1)
        # Legs
        cv2.rectangle(frame, (cx2 - 12, cy2 - 10), (cx2 - 2, cy2 + 25), (40, 40, 40), -1)
        cv2.rectangle(frame, (cx2 + 2, cy2 - 10), (cx2 + 12, cy2 + 25), (40, 40, 40), -1)
        
        out.write(frame)
        
    out.release()
    print(f"Generated test video at {output_path}")

if __name__ == "__main__":
    generate_test_players_video()

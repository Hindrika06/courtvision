import os
import cv2
import numpy as np

def create_sample_ad(filename, title, subtitle, bg_color, text_color):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    w, h = 800, 400
    # Create BGRA canvas
    img = np.zeros((h, w, 4), dtype=np.uint8)
    
    # Outer border / rounded rect background (solid/opaque)
    margin = 10
    cv2.rectangle(img, (margin, margin), (w - margin, h - margin), bg_color + (255,), -1)
    cv2.rectangle(img, (margin, margin), (w - margin, h - margin), (255, 255, 255, 255), 8)
    
    # Text rendering
    font = cv2.FONT_HERSHEY_DUPLEX
    
    # Title
    t_scale = 2.2
    t_thick = 4
    (tw, th), _ = cv2.getTextSize(title, font, t_scale, t_thick)
    tx = (w - tw) // 2
    ty = (h + th) // 2 - 20
    cv2.putText(img, title, (tx, ty), font, t_scale, text_color + (255,), t_thick, cv2.LINE_AA)
    
    # Subtitle
    s_scale = 1.0
    s_thick = 2
    (sw, sh), _ = cv2.getTextSize(subtitle, font, s_scale, s_thick)
    sx = (w - sw) // 2
    sy = ty + 50
    cv2.putText(img, subtitle, (sx, sy), font, s_scale, (230, 230, 230, 255), s_thick, cv2.LINE_AA)
    
    cv2.imwrite(filename, img)
    print(f"Created ad: {filename}")

if __name__ == "__main__":
    create_sample_ad("ads/ad1.png", "COURTVISION", "VIRTUAL ADS SYSTEM", (180, 50, 20), (255, 255, 255))
    create_sample_ad("ads/ad2.png", "HYPERSPORTS", "PREMIUM SPONSOR", (20, 100, 180), (255, 255, 255))

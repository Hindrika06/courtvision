"""Loading and blending ads."""
import cv2
import numpy as np


def load_ad(path):
    """Load a PNG/JPG as BGRA uint8 (adds an opaque alpha if the file has none)."""
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Could not read ad image: {path}")
    if img.dtype == np.uint16:
        img = (img / 257).astype(np.uint8)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    elif img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    return img


def blend_ad(frame, ad_pm, ad_a, opacity=0.85, allow=None):
    """
    Blend a warped ad onto the frame.

    allow: optional float mask (0..1, HxW). 1 = ad may be drawn, 0 = keep original.
           (Later: this will be the player-protection mask.)
    """
    if allow is None:
        k = np.float32(opacity)
        a = ad_a * k
        pm = ad_pm * k
    else:
        k = allow.astype(np.float32) * opacity
        a = ad_a * k
        pm = ad_pm * k[:, :, None]
    out = frame.astype(np.float32) * (1.0 - a)[:, :, None] + pm
    return np.clip(out, 0, 255).astype(np.uint8)
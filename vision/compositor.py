"""Loading and blending ads with high-quality surface-conforming rendering."""
import cv2
import numpy as np
from vision.homography import rect_to_quad


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


def prepare_warped_ad(ad_img, H, x0, y0, x1, y1, frame_size, adapt_lighting=True, bg_frame=None):
    """
    Warp an ad image from court coordinates (metres) to camera frame perspective
    with anti-aliased edge resampling and optional court surface lighting adaptation.

    ad_img: uint8 image (BGRA)
    H: 3x3 homography matrix (court metres -> image pixels)
    x0, y0, x1, y1: court bounding rectangle in metres
    frame_size: tuple (width, height)
    adapt_lighting: bool, whether to adapt ad brightness to court lighting
    bg_frame: optional original frame used for local court lighting estimation

    Returns:
        ad_pm: premultiplied float32 (HxWx3)
        ad_a: float32 alpha (HxW) range 0..1
    """
    w_frame, h_frame = int(frame_size[0]), int(frame_size[1])
    h_ad, w_ad = ad_img.shape[:2]

    # Destination quad in camera pixel coordinates
    dst_quad = rect_to_quad(H, x0, y0, x1, y1)
    src_quad = np.float32([[0, 0], [w_ad, 0], [w_ad, h_ad], [0, h_ad]])

    H_ad = cv2.getPerspectiveTransform(src_quad, np.float32(dst_quad))

    # Anti-aliased perspective warp using INTER_CUBIC / INTER_LINEAR
    warped = cv2.warpPerspective(ad_img, H_ad, (w_frame, h_frame), flags=cv2.INTER_CUBIC)

    if warped.shape[2] == 4:
        b, g, r, a = cv2.split(warped)
        ad_a = (a / 255.0).astype(np.float32)
        
        # Smooth alpha edge boundary to prevent stair-step anti-aliasing artifacts
        if np.any(ad_a > 0):
            kernel_edge = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            ad_a = cv2.GaussianBlur(ad_a, (3, 3), 0.5)

        ad_bgr = cv2.merge([b, g, r]).astype(np.float32)
        ad_pm = ad_bgr * ad_a[:, :, None]
    else:
        mask_src = np.ones((h_ad, w_ad), dtype=np.float32)
        ad_a = cv2.warpPerspective(mask_src, H_ad, (w_frame, h_frame), flags=cv2.INTER_LINEAR)
        ad_a = cv2.GaussianBlur(ad_a, (3, 3), 0.5)
        ad_pm = warped.astype(np.float32) * ad_a[:, :, None]

    # Court surface lighting adaptation (applied ONLY to ad layer)
    if adapt_lighting and bg_frame is not None and bg_frame.shape[:2] == (h_frame, w_frame):
        ad_region = ad_a > 0.1
        if np.any(ad_region):
            # Compute luminance of underlying court region
            bg_gray = cv2.cvtColor(bg_frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
            mean_court_lum = float(np.mean(bg_gray[ad_region]))
            # Calculate lighting scaling factor (clamped conservatively between 0.88 and 1.12)
            l_factor = np.clip(mean_court_lum / 120.0, 0.88, 1.12)
            ad_pm = ad_pm * l_factor

    return ad_pm, ad_a


def blend_ad(frame, ad_pm, ad_a, opacity=0.85, allow=None):
    """
    Blend a warped ad onto the frame.

    opacity: default 0.85 for physical court sticker realism.
    allow: optional float mask (0..1, HxW). 1 = ad may be drawn, 0 = keep original.
           (Used for player-protection mask: allow = 1.0 - player_mask)
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
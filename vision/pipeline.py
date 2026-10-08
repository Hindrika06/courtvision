"""
Central CourtVision Pipeline abstraction.
Connects court calibration, homography, player detection/segmentation, tracking, fine-object (racket) detection, ad rendering, and compositing.
"""
import json
import os
import time
import cv2
import numpy as np

from vision.homography import build_homography, load_court
from vision.compositor import load_ad, prepare_warped_ad, blend_ad
from vision.player_detector import PlayerDetector
from vision.player_tracker import PlayerTracker
from vision.player_mask import PlayerMaskGenerator
from vision.fine_object_detector import FineObjectDetector


class CourtVisionPipeline:
    """
    Main reusable processing engine for CourtVision.
    Supports both pre-recorded video files and live webcam feeds.
    """

    def __init__(
        self,
        court_config_path="config/court.json",
        ads_config_path="config/ads.json",
        model_name="yolov8n-seg.pt",
        conf_thresh=0.25,
        imgsz=640,
        device="cpu",
        frame_skip=0,
        racket_protection=False,
        racket_model=None,
        racket_conf=0.25,
        racket_imgsz=None
    ):
        self.court_config_path = court_config_path
        self.ads_config_path = ads_config_path
        self.frame_skip = frame_skip
        self.frame_count = 0
        self.racket_protection = racket_protection

        # Load court calibration
        self.court_config = self._load_court_config(court_config_path)

        # Load ads configuration
        self.ads = self._load_ads_config(ads_config_path)

        # Initialize AI modules ONCE at startup
        self.detector = PlayerDetector(
            model_name=model_name,
            conf_thresh=conf_thresh,
            imgsz=imgsz,
            device=device
        )
        self.tracker = PlayerTracker()
        self.mask_generator = PlayerMaskGenerator(refine_mask=True)

        # Optional fine-object / racket detector
        racket_model_name = racket_model or model_name
        racket_sz = racket_imgsz or imgsz
        shared_model = self.detector.model if (racket_model_name == model_name or racket_model is None) else None
        
        self.racket_detector = FineObjectDetector(
            model_name=racket_model_name,
            conf_thresh=racket_conf,
            imgsz=racket_sz,
            device=device,
            target_classes=[38], # Class 38 = tennis/badminton racket in COCO
            existing_model=shared_model
        )
        self.racket_detector.enabled = racket_protection

        # Detailed performance metrics (ms)
        self.fps = 0.0
        self.inference_time_ms = 0.0
        self.tracking_time_ms = 0.0
        self.mask_gen_time_ms = 0.0
        self.ad_warp_time_ms = 0.0
        self.compositing_time_ms = 0.0
        self.total_frame_time_ms = 0.0
        self._last_time = time.perf_counter()
        self._cached_tracked_players = []
        self._cached_racket_detections = []
        self._res_warned = False

    def _load_court_config(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Court calibration file not found at: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_ads_config(self, path):
        if not os.path.exists(path):
            print(f"[Pipeline] Warning: Ads config not found at {path}, using defaults.")
            return []

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ads_list = []
        for ad_def in data.get("ads", []):
            img_path = ad_def.get("image")
            if not os.path.exists(img_path):
                print(f"[Pipeline] Warning: Ad image missing at '{img_path}', skipping.")
                continue
            try:
                ad_img = load_ad(img_path)
                ads_list.append({
                    "name": ad_def.get("name", "ad"),
                    "image": ad_img,
                    "x0": float(ad_def.get("x0", 0.0)),
                    "y0": float(ad_def.get("y0", 0.0)),
                    "x1": float(ad_def.get("x1", 1.0)),
                    "y1": float(ad_def.get("y1", 1.0)),
                    "opacity": float(ad_def.get("opacity", 0.85)) # Production default 0.85 opacity for court sticker realism
                })
            except Exception as e:
                print(f"[Pipeline] Error loading ad image '{img_path}': {e}")

        return ads_list

    def get_homography(self, frame_w, frame_h):
        """
        Build homography matrix, automatically scaling calibration court points
        if frame resolution differs from calibration frame size.
        """
        calib_pts = self.court_config["court_points"]
        calib_w, calib_h = self.court_config.get("frame_size", [frame_w, frame_h])

        if calib_w != frame_w or calib_h != frame_h:
            if not self._res_warned:
                print(f"[Pipeline] Calibration size {calib_w}x{calib_h} differs from camera {frame_w}x{frame_h}. Scaling homography points proportionally.")
                print("[Pipeline] Advisory: If camera position has moved, please recalibrate using --calibrate.")
                self._res_warned = True

            sx = frame_w / float(calib_w)
            sy = frame_h / float(calib_h)
            pts = [[p[0] * sx, p[1] * sy] for p in calib_pts]
        else:
            pts = calib_pts

        return build_homography(pts)

    def process_frame(self, frame, return_debug=False):
        """
        Process a single frame:
        Input Source -> Frame Capture -> Court Processing -> Player Processing
        -> Fine Object (Racket) Processing -> Advertisement Surface Rendering -> Compositing -> Output Frame
        """
        if frame is None:
            return None if not return_debug else (None, {})

        t0 = time.perf_counter()
        h, w = frame.shape[:2]

        # 1. Court Homography
        H = self.get_homography(w, h)

        # 2. Player Detection & Segmentation
        self.frame_count += 1
        should_detect = (self.frame_skip == 0) or (self.frame_count % (self.frame_skip + 1) == 1)

        t_det_start = time.perf_counter()
        if should_detect:
            detections = self.detector.detect_and_segment(frame)
            if self.racket_protection:
                racket_detections = self.racket_detector.detect_and_segment(frame)
                self._cached_racket_detections = racket_detections
            else:
                racket_detections = []
        else:
            detections = []
            racket_detections = self._cached_racket_detections
        t_det_end = time.perf_counter()
        self.inference_time_ms = (t_det_end - t_det_start) * 1000.0

        # 3. Tracking
        t_track_start = time.perf_counter()
        if should_detect:
            tracked_players = self.tracker.update(detections)
            self._cached_tracked_players = tracked_players
        else:
            tracked_players = self.tracker.update([])
            if not tracked_players and self._cached_tracked_players:
                self._cached_tracked_players = []
            else:
                tracked_players = self._cached_tracked_players
        t_track_end = time.perf_counter()
        self.tracking_time_ms = (t_track_end - t_track_start) * 1000.0

        # 4. Protection Mask Generation (Person + Fine Objects)
        t_mask_start = time.perf_counter()
        player_mask, allow_mask = self.mask_generator.generate(
            tracked_players, (h, w), fine_objects=racket_detections
        )
        t_mask_end = time.perf_counter()
        self.mask_gen_time_ms = (t_mask_end - t_mask_start) * 1000.0

        # 5. Surface-Conforming Advertisement Rendering & Compositing
        t_warp_start = time.perf_counter()
        ad_layer = np.zeros((h, w, 3), dtype=np.uint8)

        # Pre-warp ads with anti-aliasing and court surface lighting adaptation
        warped_ads_cache = []
        for ad in self.ads:
            ad_pm, ad_a = prepare_warped_ad(
                ad["image"], H, ad["x0"], ad["y0"], ad["x1"], ad["y1"], (w, h),
                adapt_lighting=True, bg_frame=frame
            )
            warped_ads_cache.append((ad, ad_pm, ad_a))
            ad_layer = blend_ad(ad_layer, ad_pm, ad_a, opacity=ad["opacity"])
        t_warp_end = time.perf_counter()
        self.ad_warp_time_ms = (t_warp_end - t_warp_start) * 1000.0

        t_comp_start = time.perf_counter()
        out_frame = frame.copy()
        for ad, ad_pm, ad_a in warped_ads_cache:
            out_frame = blend_ad(
                out_frame, ad_pm, ad_a, opacity=ad["opacity"], allow=allow_mask
            )
        t_comp_end = time.perf_counter()
        self.compositing_time_ms = (t_comp_end - t_comp_start) * 1000.0

        # Timing breakdown & FPS calculation
        t_end = time.perf_counter()
        self.total_frame_time_ms = (t_end - t0) * 1000.0
        now = time.perf_counter()
        dt = now - self._last_time
        self._last_time = now
        if dt > 0:
            inst_fps = 1.0 / dt
            self.fps = 0.9 * self.fps + 0.1 * inst_fps if self.fps > 0 else inst_fps

        if return_debug:
            racket_mask = np.zeros((h, w), dtype=np.uint8)
            for r_det in racket_detections:
                m = r_det.get('mask')
                if m is not None:
                    if m.shape[:2] != (h, w):
                        m = cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
                    racket_mask = np.bitwise_or(racket_mask, (m > 0).astype(np.uint8))

            debug_info = {
                "original": frame,
                "player_mask": player_mask,
                "racket_mask": racket_mask,
                "ad_layer": ad_layer,
                "composited": out_frame,
                "allow_mask": allow_mask,
                "tracked_players": tracked_players,
                "racket_detections": racket_detections
            }
            return out_frame, debug_info

        return out_frame

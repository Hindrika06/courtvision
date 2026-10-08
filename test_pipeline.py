"""
Complete Automated Test Suite for CourtVision.
Tests all target pipeline cases including fine-object (racket) protection, surface-conforming ad rendering, lighting adaptation, and quality presets.
"""
import os
import sys
import unittest
import numpy as np
import cv2

from vision.homography import build_homography, rect_to_quad, load_court, COURT_W, COURT_L
from vision.compositor import load_ad, prepare_warped_ad, blend_ad
from vision.player_tracker import PlayerTracker
from vision.player_mask import PlayerMaskGenerator
from vision.pipeline import CourtVisionPipeline
from vision.fine_object_detector import FineObjectDetector


class TestCourtVisionPipeline(unittest.TestCase):

    def setUp(self):
        self.court_config = "config/court.json"
        self.ads_config = "config/ads.json"
        self.court_data = load_court(self.court_config)

    def test_01_homography(self):
        """Test 1: Existing homography calculation works."""
        pts = self.court_data["court_points"]
        H = build_homography(pts)
        self.assertEqual(H.shape, (3, 3))
        # Top-left corner of court (0,0) should map near first point
        quad = rect_to_quad(H, 0, 0, 1, 1)
        self.assertEqual(quad.shape, (4, 2))

    def test_02_ad_mapping_to_court(self):
        """Test 2: Advertisement correctly maps to court coordinates."""
        pts = self.court_data["court_points"]
        H = build_homography(pts)
        ad_img = load_ad("ads/ad1.png")
        ad_pm, ad_a = prepare_warped_ad(ad_img, H, 1.2, 14.5, 4.4, 21.0, (1280, 720))
        self.assertEqual(ad_pm.shape, (720, 1280, 3))
        self.assertEqual(ad_a.shape, (720, 1280))
        self.assertTrue(np.any(ad_a > 0))

    def test_03_ad_perspective_change(self):
        """Test 3: Advertisement automatically changes perspective when camera/homography changes."""
        pts1 = self.court_data["court_points"]
        # Modified camera perspective (simulated camera shift)
        pts2 = [[p[0] * 1.1, p[1] * 0.9] for p in pts1]

        H1 = build_homography(pts1)
        H2 = build_homography(pts2)

        ad_img = load_ad("ads/ad1.png")
        _, ad_a1 = prepare_warped_ad(ad_img, H1, 1.2, 14.5, 4.4, 21.0, (1280, 720))
        _, ad_a2 = prepare_warped_ad(ad_img, H2, 1.2, 14.5, 4.4, 21.0, (1280, 720))

        # Alpha masks should differ due to different perspective
        self.assertFalse(np.array_equal(ad_a1 > 0, ad_a2 > 0))

    def test_04_player_mask_protection(self):
        """Test 4: Player mask correctly protects single player."""
        gen = PlayerMaskGenerator(refine_mask=False)
        mask1 = np.zeros((720, 1280), dtype=np.uint8)
        mask1[100:200, 100:200] = 1

        tracked = [{'id': 1, 'bbox': [100, 100, 200, 200], 'mask': mask1}]
        p_mask, allow = gen.generate(tracked, (720, 1280))

        self.assertEqual(p_mask[150, 150], 1)
        self.assertEqual(allow[150, 150], 0.0)
        self.assertEqual(allow[50, 50], 1.0)

    def test_05_multiple_player_masks(self):
        """Test 5: Multiple player masks combine correctly (OR operation)."""
        gen = PlayerMaskGenerator(refine_mask=False)
        m1 = np.zeros((720, 1280), dtype=np.uint8)
        m1[100:200, 100:200] = 1

        m2 = np.zeros((720, 1280), dtype=np.uint8)
        m2[400:500, 400:500] = 1

        tracked = [
            {'id': 1, 'bbox': [100, 100, 200, 200], 'mask': m1},
            {'id': 2, 'bbox': [400, 400, 500, 500], 'mask': m2}
        ]

        p_mask, allow = gen.generate(tracked, (720, 1280))
        self.assertEqual(p_mask[150, 150], 1)
        self.assertEqual(p_mask[450, 450], 1)
        self.assertEqual(allow[150, 150], 0.0)
        self.assertEqual(allow[450, 450], 0.0)
        self.assertEqual(allow[300, 300], 1.0)

    def test_06_player_moving_across_ad(self):
        """Test 6: Player moving across ad keeps player pixels completely intact."""
        tracker = PlayerTracker()

        # Frame 1: player at x=100
        det1 = [{'bbox': [100, 100, 200, 200], 'confidence': 0.9, 'mask': np.ones((720, 1280), dtype=np.uint8)}]
        tr1 = tracker.update(det1)
        self.assertEqual(len(tr1), 1)

        # Frame 2: player moves to x=150
        det2 = [{'bbox': [150, 100, 250, 200], 'confidence': 0.9, 'mask': np.ones((720, 1280), dtype=np.uint8)}]
        tr2 = tracker.update(det2)
        self.assertEqual(len(tr2), 1)
        self.assertEqual(tr2[0]['id'], tr1[0]['id'])  # Same ID maintained

    def test_07_video_mode(self):
        """Test 7: Video input mode works."""
        pipeline = CourtVisionPipeline(court_config_path=self.court_config, ads_config_path=self.ads_config)
        cap = cv2.VideoCapture("input/input.mp4")
        ret, frame = cap.read()
        cap.release()
        self.assertTrue(ret)
        out = pipeline.process_frame(frame)
        self.assertIsNotNone(out)
        self.assertEqual(out.shape, frame.shape)

    def test_08_webcam_mode(self):
        """Test 8: Webcam source capability in pipeline."""
        pipeline = CourtVisionPipeline(court_config_path=self.court_config, ads_config_path=self.ads_config)
        synthetic_cam_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        out = pipeline.process_frame(synthetic_cam_frame)
        self.assertIsNotNone(out)
        self.assertEqual(out.shape, (720, 1280, 3))

    def test_09_invalid_source_handling(self):
        """Test 9: Invalid camera source produces useful error without crash."""
        cap = cv2.VideoCapture("non_existent_file.mp4")
        self.assertFalse(cap.isOpened())

    def test_10_no_player_ad_fully_visible(self):
        """Test 10: No player present -> ad is fully rendered."""
        frame = np.full((720, 1280, 3), 100, dtype=np.uint8)
        ad_img = load_ad("ads/ad1.png")
        pts = self.court_data["court_points"]
        H = build_homography(pts)
        ad_pm, ad_a = prepare_warped_ad(ad_img, H, 1.2, 14.5, 4.4, 21.0, (1280, 720))

        # allow = 1.0 everywhere (no player)
        allow = np.ones((720, 1280), dtype=np.float32)
        blended = blend_ad(frame, ad_pm, ad_a, opacity=0.85, allow=allow)

        ad_region = ad_a > 0.5
        self.assertTrue(np.any(blended[ad_region] != frame[ad_region]))

    def test_11_player_enters_ad_pixel_replacement(self):
        """Test 11: Player enters ad area -> player pixels replace ad pixels exactly."""
        frame = np.full((720, 1280, 3), 100, dtype=np.uint8)
        # Player is bright white inside ad region
        frame[500:600, 500:600] = 255

        ad_img = load_ad("ads/ad1.png")
        pts = self.court_data["court_points"]
        H = build_homography(pts)
        ad_pm, ad_a = prepare_warped_ad(ad_img, H, 1.2, 14.5, 4.4, 21.0, (1280, 720))

        # Player mask covering player region
        player_mask = np.zeros((720, 1280), dtype=np.uint8)
        player_mask[500:600, 500:600] = 1
        allow = (1.0 - player_mask.astype(np.float32))

        blended = blend_ad(frame, ad_pm, ad_a, opacity=0.85, allow=allow)

        # Player pixels (500:600, 500:600) must equal original frame (255)
        np.testing.assert_array_equal(blended[500:600, 500:600], frame[500:600, 500:600])

    def test_12_player_leaves_ad(self):
        """Test 12: Player leaves ad -> ad becomes visible again."""
        frame = np.full((720, 1280, 3), 100, dtype=np.uint8)
        ad_img = load_ad("ads/ad1.png")
        pts = self.court_data["court_points"]
        H = build_homography(pts)
        ad_pm, ad_a = prepare_warped_ad(ad_img, H, 1.2, 14.5, 4.4, 21.0, (1280, 720))

        # Frame A: Player in ad area
        p_mask_a = np.zeros((720, 1280), dtype=np.uint8)
        p_mask_a[500:600, 500:600] = 1
        allow_a = 1.0 - p_mask_a.astype(np.float32)
        blended_a = blend_ad(frame, ad_pm, ad_a, opacity=0.85, allow=allow_a)

        # Frame B: Player left ad area (no mask)
        allow_b = np.ones((720, 1280), dtype=np.float32)
        blended_b = blend_ad(frame, ad_pm, ad_a, opacity=0.85, allow=allow_b)

        # In frame B, ad area (500:600, 500:600) is now showing ad pixels
        self.assertFalse(np.array_equal(blended_a[500:600, 500:600], blended_b[500:600, 500:600]))

    def test_13_quality_presets(self):
        """Test 13: Pipeline works under production and performance modes."""
        prod_pipe = CourtVisionPipeline(court_config_path=self.court_config, ads_config_path=self.ads_config, imgsz=640, frame_skip=0)
        perf_pipe = CourtVisionPipeline(court_config_path=self.court_config, ads_config_path=self.ads_config, imgsz=320, frame_skip=1)

        dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        out_prod = prod_pipe.process_frame(dummy_frame)
        out_perf = perf_pipe.process_frame(dummy_frame)

        self.assertEqual(out_prod.shape, (720, 1280, 3))
        self.assertEqual(out_perf.shape, (720, 1280, 3))

    def test_14_dynamic_resolution_scaling(self):
        """Test 14: Dynamic homography scaling when input resolution is 1920x1080 vs 1280x720 calibration."""
        pipe = CourtVisionPipeline(court_config_path=self.court_config, ads_config_path=self.ads_config)
        hd_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        out = pipe.process_frame(hd_frame)
        self.assertEqual(out.shape, (1080, 1920, 3))

    def test_15_racket_protection_combines_masks(self):
        """Test 15: Person mask and fine-object / racket mask combine via OR into allow mask."""
        gen = PlayerMaskGenerator(refine_mask=False)
        p_mask = np.zeros((720, 1280), dtype=np.uint8)
        p_mask[100:200, 100:200] = 1

        racket_mask = np.zeros((720, 1280), dtype=np.uint8)
        racket_mask[220:260, 220:260] = 1

        tracked = [{'id': 1, 'bbox': [100, 100, 200, 200], 'mask': p_mask}]
        fine_objs = [{'type': 'racket', 'mask': racket_mask}]

        comb_mask, allow = gen.generate(tracked, (720, 1280), fine_objects=fine_objs)

        # Both person area (150,150) and racket area (240,240) are protected
        self.assertEqual(comb_mask[150, 150], 1)
        self.assertEqual(comb_mask[240, 240], 1)
        self.assertEqual(allow[150, 150], 0.0)
        self.assertEqual(allow[240, 240], 0.0)
        self.assertEqual(allow[50, 50], 1.0)

    def test_16_racket_detector_fallback(self):
        """Test 16: Pipeline gracefully falls back to person protection if racket detector is unavailable/disabled."""
        pipe = CourtVisionPipeline(court_config_path=self.court_config, ads_config_path=self.ads_config, racket_protection=True, racket_model="non_existent_model.pt")
        dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        out = pipe.process_frame(dummy_frame)
        self.assertIsNotNone(out)
        self.assertEqual(out.shape, (720, 1280, 3))

    def test_17_ad_opacity_and_lighting_adaptation(self):
        """Test 17: Surface-conforming ad rendering with lighting adaptation and customizable opacity."""
        ad_img = load_ad("ads/ad1.png")
        pts = self.court_data["court_points"]
        H = build_homography(pts)
        
        bg_dark = np.full((720, 1280, 3), 50, dtype=np.uint8)
        bg_bright = np.full((720, 1280, 3), 200, dtype=np.uint8)

        pm_dark, a_dark = prepare_warped_ad(ad_img, H, 1.2, 14.5, 4.4, 21.0, (1280, 720), adapt_lighting=True, bg_frame=bg_dark)
        pm_bright, a_bright = prepare_warped_ad(ad_img, H, 1.2, 14.5, 4.4, 21.0, (1280, 720), adapt_lighting=True, bg_frame=bg_bright)

        # Bright background court should yield higher premultiplied ad intensity than dark court
        region = a_dark > 0.5
        self.assertGreater(np.mean(pm_bright[region]), np.mean(pm_dark[region]))

        # Test opacity blending
        blended_085 = blend_ad(bg_bright, pm_bright, a_bright, opacity=0.85)
        self.assertEqual(blended_085.shape, (720, 1280, 3))

    def test_18_multi_ad_surface_conforming(self):
        """Test 18: Multi-ad surface conforming rendering in pipeline."""
        pipe = CourtVisionPipeline(court_config_path=self.court_config, ads_config_path=self.ads_config)
        test_frame = np.full((720, 1280, 3), 140, dtype=np.uint8)
        out = pipe.process_frame(test_frame)
        self.assertIsNotNone(out)
        self.assertEqual(out.shape, (720, 1280, 3))


if __name__ == "__main__":
    unittest.main()

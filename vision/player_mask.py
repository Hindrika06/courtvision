"""
Player Protection Mask Generator for CourtVision.
Combines multiple player segmentation masks and optional fine-object (racket) masks into a single protection mask.
"""
import cv2
import numpy as np


class PlayerMaskGenerator:
    """
    Combines individual player masks and fine-object masks into a single protection mask.
    Computes allow mask for alpha compositing.
    """

    def __init__(self, refine_mask=True):
        self.refine_mask = refine_mask

    def generate(self, tracked_players, frame_shape, fine_objects=None):
        """
        tracked_players: list of dicts containing 'mask' key
        frame_shape: (H, W) or (H, W, C)
        fine_objects: optional list of dicts containing 'mask' key (e.g. rackets)

        Returns:
            player_mask: uint8 array (HxW) where 1 = protected pixel, 0 = non-protected
            allow_mask: float32 array (HxW) where 1.0 = ad allowed, 0.0 = player/racket protected
        """
        h, w = frame_shape[:2]
        player_mask = np.zeros((h, w), dtype=np.uint8)

        # 1. Person protection masks
        for p in tracked_players:
            m = p.get('mask')
            if m is not None:
                if m.shape[:2] != (h, w):
                    m = cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
                player_mask = np.bitwise_or(player_mask, (m > 0).astype(np.uint8))

        # 2. Fine-object / Racket protection masks
        if fine_objects:
            for fo in fine_objects:
                m = fo.get('mask')
                if m is not None:
                    if m.shape[:2] != (h, w):
                        m = cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
                    player_mask = np.bitwise_or(player_mask, (m > 0).astype(np.uint8))

        if self.refine_mask and np.any(player_mask):
            # Minimal morphological closing to fill tiny internal holes without blurring edges
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            player_mask = cv2.morphologyEx(player_mask, cv2.MORPH_CLOSE, kernel)

        # allow = 1.0 for ad, 0.0 for player original frame
        allow_mask = (1.0 - player_mask.astype(np.float32))

        return player_mask, allow_mask

"""
Fine-Object / Racket Detection & Segmentation Module for CourtVision.
Detects fine sports equipment (e.g. rackets, COCO class 38) using segmentation models.
Loads model ONCE at startup with graceful fallback if unavailable.
"""
import os
import cv2
import numpy as np


class FineObjectDetector:
    """
    Fine-object detector for sports equipment and rackets.
    Supports COCO class 38 (tennis/badminton racket) or custom fine-object segmentation models.
    """

    def __init__(self, model_name="yolov8n-seg.pt", conf_thresh=0.25, imgsz=640, device="cpu", target_classes=[38], existing_model=None):
        self.model_name = model_name
        self.conf_thresh = conf_thresh
        self.imgsz = imgsz
        self.device = device
        self.target_classes = target_classes
        self.model = existing_model
        self.enabled = True

        if self.model is None:
            self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            os.makedirs("models", exist_ok=True)
            target_path = os.path.join("models", os.path.basename(self.model_name))
            model_file = target_path if os.path.exists(target_path) else self.model_name
            self.model = YOLO(model_file)
            print(f"[FineObjectDetector] Loaded fine-object segmentation model: {model_file}")
        except Exception as e:
            print(f"[FineObjectDetector] Warning: Fine-object model '{self.model_name}' not available ({e}). Person protection remains fully active.")
            self.model = None

    def detect_and_segment(self, frame):
        """
        Detect fine objects (e.g. rackets) in frame and generate binary segmentation masks.

        Returns list of detection dicts:
        [
            {
                'bbox': [x1, y1, x2, y2],
                'confidence': float,
                'mask': uint8 array (HxW) with 1 for object, 0 for background,
                'type': 'racket'
            },
            ...
        ]
        """
        if not self.enabled or frame is None or self.model is None:
            return []

        h, w = frame.shape[:2]

        try:
            results = self.model.predict(
                source=frame,
                classes=self.target_classes,
                conf=self.conf_thresh,
                imgsz=self.imgsz,
                device=self.device,
                verbose=False
            )
        except Exception as e:
            print(f"[FineObjectDetector] Inference error: {e}")
            return []

        detections = []
        if not results:
            return detections

        res = results[0]
        if res.boxes is None or len(res.boxes) == 0:
            return detections

        boxes = res.boxes.xyxy.cpu().numpy()
        confs = res.boxes.conf.cpu().numpy()
        has_masks = res.masks is not None and len(res.masks) > 0

        if has_masks:
            masks_data = res.masks.data.cpu().numpy()

        for i in range(len(boxes)):
            bbox = boxes[i].tolist()
            conf = float(confs[i])
            if has_masks and i < len(masks_data):
                m = masks_data[i]
                if m.shape != (h, w):
                    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)
                binary_mask = (m > 0.5).astype(np.uint8)
            else:
                binary_mask = np.zeros((h, w), dtype=np.uint8)
                x1, y1, x2, y2 = map(int, bbox)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                binary_mask[y1:y2, x1:x2] = 1

            detections.append({
                'bbox': bbox,
                'confidence': conf,
                'mask': binary_mask,
                'type': 'racket'
            })

        return detections

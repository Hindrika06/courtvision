"""
Person Detection & Segmentation Module for CourtVision.
Uses a lightweight segmentation model (e.g. YOLOv8n-seg) loaded ONCE at startup.
"""
import os
import cv2
import numpy as np


class PlayerDetector:
    """
    Player detector and segmenter.
    Loads the segmentation model ONCE at startup to generate pixel-level masks.
    """

    def __init__(self, model_name="yolov8n-seg.pt", conf_thresh=0.25, imgsz=640, device="cpu"):
        self.model_name = model_name
        self.conf_thresh = conf_thresh
        self.imgsz = imgsz
        self.device = device
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            # Check if model exists locally or download weights to models/ directory
            os.makedirs("models", exist_ok=True)
            target_path = os.path.join("models", os.path.basename(self.model_name))
            model_file = target_path if os.path.exists(target_path) else self.model_name
            self.model = YOLO(model_file)
            print(f"[PlayerDetector] Loaded segmentation model: {model_file} on device: {self.device}")
        except Exception as e:
            print(f"[PlayerDetector] Warning: Ultralytics YOLO model '{self.model_name}' not available ({e}).")
            self.model = None

    def detect_and_segment(self, frame):
        """
        Detect persons in the frame and generate binary segmentation masks.

        Returns list of detection dictionaries:
        [
            {
                'bbox': [x1, y1, x2, y2],
                'confidence': float,
                'mask': uint8 array (HxW) with 1 for person, 0 for background
            },
            ...
        ]
        """
        if frame is None:
            return []

        h, w = frame.shape[:2]

        if self.model is None:
            return []

        try:
            results = self.model.predict(
                source=frame,
                classes=[0],  # Class 0 = person in COCO dataset
                conf=self.conf_thresh,
                imgsz=self.imgsz,
                device=self.device,
                verbose=False
            )
        except Exception as e:
            print(f"[PlayerDetector] Inference error: {e}")
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
                # Fallback to rectangular mask if segment mask is missing
                binary_mask = np.zeros((h, w), dtype=np.uint8)
                x1, y1, x2, y2 = map(int, bbox)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                binary_mask[y1:y2, x1:x2] = 1

            detections.append({
                'bbox': bbox,
                'confidence': conf,
                'mask': binary_mask
            })

        return detections

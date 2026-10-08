"""
Player Tracking Module for CourtVision.
Tracks detected persons across frames using IoU / bounding box association.
"""
import numpy as np


class PlayerTracker:
    """
    Tracks multiple players across consecutive frames to maintain identity stability and update masks.
    """

    def __init__(self, max_disappeared=15, iou_thresh=0.3):
        self.next_id = 1
        self.tracked_players = {}  # pid -> {'bbox': ..., 'mask': ..., 'disappeared': int}
        self.max_disappeared = max_disappeared
        self.iou_thresh = iou_thresh

    def update(self, detections):
        """
        Update tracker with new frame detections.

        detections: list of dicts with keys 'bbox', 'mask', 'confidence'
        Returns: list of dicts: [{'id': int, 'bbox': list, 'mask': np.ndarray}, ...]
        """
        if not detections:
            to_delete = []
            for pid in self.tracked_players:
                self.tracked_players[pid]['disappeared'] += 1
                if self.tracked_players[pid]['disappeared'] > self.max_disappeared:
                    to_delete.append(pid)
            for pid in to_delete:
                del self.tracked_players[pid]
            return self.get_tracked_list()

        if not self.tracked_players:
            for det in detections:
                self.tracked_players[self.next_id] = {
                    'bbox': det['bbox'],
                    'mask': det['mask'],
                    'disappeared': 0
                }
                self.next_id += 1
            return self.get_tracked_list()

        track_ids = list(self.tracked_players.keys())
        track_boxes = [self.tracked_players[pid]['bbox'] for pid in track_ids]
        det_boxes = [d['bbox'] for d in detections]

        iou_matrix = np.zeros((len(track_ids), len(detections)), dtype=np.float32)
        for i, tb in enumerate(track_boxes):
            for j, db in enumerate(det_boxes):
                iou_matrix[i, j] = self.compute_iou(tb, db)

        matched_tracks = set()
        matched_dets = set()

        if iou_matrix.size > 0:
            while True:
                max_idx = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
                max_iou = iou_matrix[max_idx]
                if max_iou < self.iou_thresh:
                    break
                t_idx, d_idx = max_idx
                if t_idx in matched_tracks or d_idx in matched_dets:
                    iou_matrix[t_idx, d_idx] = -1.0
                    continue

                pid = track_ids[t_idx]
                self.tracked_players[pid]['bbox'] = detections[d_idx]['bbox']
                self.tracked_players[pid]['mask'] = detections[d_idx]['mask']
                self.tracked_players[pid]['disappeared'] = 0

                matched_tracks.add(t_idx)
                matched_dets.add(d_idx)
                iou_matrix[t_idx, :] = -1.0
                iou_matrix[:, d_idx] = -1.0

        # Mark unmatched tracked objects as disappeared
        to_delete = []
        for i, pid in enumerate(track_ids):
            if i not in matched_tracks:
                self.tracked_players[pid]['disappeared'] += 1
                if self.tracked_players[pid]['disappeared'] > self.max_disappeared:
                    to_delete.append(pid)
        for pid in to_delete:
            del self.tracked_players[pid]

        # Register unmatched detections as new tracked players
        for j, det in enumerate(detections):
            if j not in matched_dets:
                self.tracked_players[self.next_id] = {
                    'bbox': det['bbox'],
                    'mask': det['mask'],
                    'disappeared': 0
                }
                self.next_id += 1

        return self.get_tracked_list()

    def get_tracked_list(self):
        return [
            {
                'id': pid,
                'bbox': data['bbox'],
                'mask': data['mask']
            }
            for pid, data in self.tracked_players.items()
            if data['disappeared'] == 0  # Only active detections for current frame
        ]

    @staticmethod
    def compute_iou(boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        inter_area = max(0.0, xB - xA) * max(0.0, yB - yA)
        boxA_area = max(0.0, boxA[2] - boxA[0]) * max(0.0, boxA[3] - boxA[1])
        boxB_area = max(0.0, boxB[2] - boxB[0]) * max(0.0, boxB[3] - boxB[1])

        denom = boxA_area + boxB_area - inter_area
        return inter_area / denom if denom > 0 else 0.0

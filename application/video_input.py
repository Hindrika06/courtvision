"""
Video Input Manager for CourtVision.
Dedicated abstraction supporting Local Webcams, Video Files, and RTSP / IP Cameras
with automatic reconnect handling, sanitized URL logging, latest-frame low-latency buffering,
and stream health monitoring.
"""
import os
import sys
import time
import json
import re
import threading
import cv2
import numpy as np


def sanitize_url(url_str):
    """
    Sanitize RTSP URLs by masking user credentials for secure UI display and logging.
    Example: 'rtsp://admin:secret123@192.168.1.100:554/stream' -> 'rtsp://192.168.1.100:554/stream'
    """
    if not isinstance(url_str, str):
        return str(url_str)
    # Mask credentials matching rtsp://username:password@host
    sanitized = re.sub(r'(rtsp://)[^@]+@', r'\1', url_str, flags=re.IGNORECASE)
    return sanitized


class ConnectionState:
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    STREAMING = "STREAMING"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"


class VideoInputManager:
    """
    Dedicated Video Input Manager handling acquisition, buffering, latency management,
    RTSP reconnect loops, and stream health stats.
    """

    def __init__(self, config_path="config/cameras.json"):
        self.config_path = config_path
        self.source_type = "webcam"  # 'webcam', 'video', 'rtsp'
        self.source_val = 0
        self.camera_name = "Camera 0"

        self.cap = None
        self.state = ConnectionState.DISCONNECTED
        self.error_message = ""

        # Reconnect Policy
        self.reconnect_enabled = True
        self.reconnect_delay = 3.0
        self.max_reconnect_attempts = 5
        self.reconnect_count = 0

        # Latest-frame low-latency buffer & threads
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.read_thread = None
        self.stop_event = threading.Event()

        # Stream Health Metrics
        self.received_frames = 0
        self.processed_frames = 0
        self.dropped_frames = 0
        self.input_fps = 0.0
        self.frame_w = 0
        self.frame_h = 0
        self._last_read_time = time.time()

        # Load initial camera profile configuration if present
        self.camera_profiles = self.load_camera_profiles()

    def load_camera_profiles(self):
        """Load camera profiles from config/cameras.json."""
        if not os.path.exists(self.config_path):
            default_profiles = {
                "cameras": [
                    {
                        "name": "Court Camera 1 (RTSP)",
                        "type": "rtsp",
                        "url": "rtsp://192.168.1.100:554/stream1",
                        "enabled": True,
                        "reconnect": True,
                        "reconnect_delay": 3
                    }
                ]
            }
            try:
                os.makedirs(os.path.dirname(self.config_path) or ".", exist_ok=True)
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(default_profiles, f, indent=4)
            except Exception:
                pass
            return default_profiles.get("cameras", [])

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("cameras", [])
        except Exception as e:
            print(f"[VideoInputManager] Warning: Error reading camera profiles: {e}")
            return []

    def open_source(self, source_type, source_val, name="Camera", reconnect=True, delay=3.0):
        """
        Open input stream (Webcam, Video File, or RTSP URL).
        Starts off-main-thread acquisition thread.
        """
        self.close_source()

        self.source_type = source_type
        self.source_val = source_val
        self.camera_name = name
        self.reconnect_enabled = reconnect
        self.reconnect_delay = delay

        # Parse source value
        if self.source_type == "webcam":
            parsed = int(source_val) if isinstance(source_val, str) and source_val.isdigit() else source_val
        elif self.source_type == "video":
            parsed = str(source_val)
            if not os.path.exists(parsed):
                self.state = ConnectionState.ERROR
                self.error_message = f"Video file not found: {parsed}"
                raise FileNotFoundError(self.error_message)
        else:  # RTSP
            parsed = str(source_val)

        sanitized = sanitize_url(str(parsed))
        print(f"[VideoInputManager] Connecting to {self.source_type.upper()}: {sanitized}...")
        self.state = ConnectionState.CONNECTING

        try:
            # Configure OpenCV VideoCapture for RTSP / webcam
            if self.source_type == "rtsp":
                # Set environment flags or timeout if supported
                self.cap = cv2.VideoCapture(parsed, cv2.CAP_FFMPEG if hasattr(cv2, 'CAP_FFMPEG') else cv2.CAP_ANY)
            elif self.source_type == "webcam" and os.name == 'nt':
                self.cap = cv2.VideoCapture(parsed, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(parsed)

            if not self.cap.isOpened():
                self.state = ConnectionState.ERROR
                self.error_message = f"Unable to connect to source: {sanitized}"
                raise RuntimeError(self.error_message)

            # Set resolution & FPS metadata
            self.frame_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
            self.frame_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720

            self.state = ConnectionState.CONNECTED
            self.reconnect_count = 0
            self.stop_event.clear()

            # Start low-latency acquisition thread
            self.read_thread = threading.Thread(target=self._acquisition_loop, daemon=True)
            self.read_thread.start()

            print(f"[VideoInputManager] Successfully connected to {name} ({self.frame_w}x{self.frame_h}).")
            return True

        except Exception as e:
            self.state = ConnectionState.ERROR
            self.error_message = str(e)
            print(f"[VideoInputManager] Connection error: {e}")
            raise e

    def _acquisition_loop(self):
        """
        Background acquisition thread for reading frames into latest-frame buffer.
        Drops stale frames if processing loop falls behind to maintain low latency.
        """
        while not self.stop_event.is_set():
            if self.cap is None or not self.cap.isOpened():
                if self.reconnect_enabled and self.source_type == "rtsp":
                    self._handle_reconnect()
                else:
                    self.state = ConnectionState.DISCONNECTED
                    break

            ret, frame = self.cap.read()
            now = time.time()

            if not ret or frame is None or frame.size == 0:
                if self.source_type == "video":
                    # Loop video file
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                elif self.reconnect_enabled and self.source_type == "rtsp":
                    print(f"[VideoInputManager] RTSP stream lost. Initiating reconnect loop...")
                    self._handle_reconnect()
                    continue
                else:
                    self.state = ConnectionState.DISCONNECTED
                    print("[VideoInputManager] Stream read failed or ended.")
                    break

            # Calculate input FPS
            dt = now - self._last_read_time
            self._last_read_time = now
            if dt > 0:
                inst_fps = 1.0 / dt
                self.input_fps = 0.9 * self.input_fps + 0.1 * inst_fps if self.input_fps > 0 else inst_fps

            self.state = ConnectionState.STREAMING

            # Bounded latest-frame update (Drop stale frame if previous hasn't been fetched)
            with self.frame_lock:
                if self.latest_frame is not None:
                    self.dropped_frames += 1
                self.latest_frame = frame
                self.received_frames += 1

            time.sleep(0.002)

    def _handle_reconnect(self):
        """Controlled reconnect loop for RTSP streams."""
        self.state = ConnectionState.RECONNECTING
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        while not self.stop_event.is_set() and self.reconnect_count < self.max_reconnect_attempts:
            self.reconnect_count += 1
            sanitized = sanitize_url(str(self.source_val))
            print(f"[VideoInputManager] Reconnecting attempt {self.reconnect_count}/{self.max_reconnect_attempts} to {sanitized} (waiting {self.reconnect_delay}s)...")
            time.sleep(self.reconnect_delay)

            try:
                self.cap = cv2.VideoCapture(str(self.source_val))
                if self.cap.isOpened():
                    ret, test_f = self.cap.read()
                    if ret and test_f is not None:
                        self.state = ConnectionState.STREAMING
                        print(f"[VideoInputManager] Reconnected successfully to {sanitized}!")
                        return
            except Exception as e:
                print(f"[VideoInputManager] Reconnect attempt failed: {e}")

        self.state = ConnectionState.ERROR
        self.error_message = f"Max reconnect attempts ({self.max_reconnect_attempts}) reached."
        print(f"[VideoInputManager] {self.error_message}")

    def get_latest_frame(self):
        """Fetch latest frame from low-latency buffer."""
        with self.frame_lock:
            frame = self.latest_frame
            self.latest_frame = None  # Consume frame
            if frame is not None:
                self.processed_frames += 1
            return frame

    def get_health_stats(self):
        """Return dict of stream health metrics."""
        return {
            "state": self.state,
            "source_type": self.source_type,
            "camera_name": self.camera_name,
            "sanitized_url": sanitize_url(str(self.source_val)),
            "input_fps": self.input_fps,
            "received_frames": self.received_frames,
            "processed_frames": self.processed_frames,
            "dropped_frames": self.dropped_frames,
            "reconnect_count": self.reconnect_count,
            "resolution": f"{self.frame_w}x{self.frame_h}",
            "error_message": self.error_message
        }

    def close_source(self):
        """Cleanly stop background acquisition thread and release VideoCapture."""
        self.stop_event.set()
        if self.read_thread is not None:
            self.read_thread.join(timeout=1.0)
            self.read_thread = None

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.state = ConnectionState.DISCONNECTED
        self.latest_frame = None
        self.received_frames = 0
        self.processed_frames = 0
        self.dropped_frames = 0
        self.input_fps = 0.0

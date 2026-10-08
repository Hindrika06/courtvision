"""
Video Output Manager for CourtVision.
Handles processed frame output, local broadcast recording (MP4), output FPS tracking,
and provides an extensible interface/stub for future network broadcast output (RTMP/SRT/NDI).
"""
import os
import sys
import time
import datetime
import cv2
import numpy as np


class NetworkOutputInterface:
    """Abstract interface for network broadcast output protocols (RTMP, SRT, NDI, RTSP server)."""

    def __init__(self, target_url=None):
        self.target_url = target_url
        self.is_connected = False

    def connect(self):
        """Establish network stream output connection."""
        pass

    def send_frame(self, frame: np.ndarray) -> bool:
        """Send a processed video frame over the network protocol."""
        return False

    def close(self):
        """Close network output stream."""
        self.is_connected = False


class NetworkOutputStub(NetworkOutputInterface):
    """Clean stub implementation for network output when no live RTMP/NDI server is present."""

    def connect(self):
        print(f"[NetworkOutputStub] Initialized network broadcast output interface stub for: {self.target_url}")
        self.is_connected = True

    def send_frame(self, frame: np.ndarray) -> bool:
        if not self.is_connected:
            return False
        # Future network streaming logic goes here (FFmpeg pipe / PyAV / NDI SDK)
        return True

    def close(self):
        print("[NetworkOutputStub] Closed network broadcast interface.")
        self.is_connected = False


class VideoOutputManager:
    """
    Video Output Manager handling:
    1. Local preview frame dispatching
    2. Local MP4 video recording with error handling & VideoWriter validation
    3. Output FPS and stats monitoring
    4. Clean network output abstraction interface
    """

    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.writer = None
        self.recording_path = None
        self.recording_active = False

        self.frames_recorded = 0
        self.output_fps = 0.0
        self._last_frame_time = time.time()

        self.network_output = None

    def start_recording(self, output_path=None, width=1280, height=720, fps=30.0):
        """
        Start recording processed broadcast frames to MP4 file.
        """
        if self.recording_active:
            self.stop_recording()

        if output_path is None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"session_{timestamp}.mp4")

        self.recording_path = output_path
        try:
            os.makedirs(os.path.dirname(self.recording_path) or ".", exist_ok=True)
        except Exception as e:
            self.recording_active = False
            self.writer = None
            err = f"Failed to create directory for path: {self.recording_path} ({e})"
            print(f"[VideoOutputManager] Error: {err}")
            raise RuntimeError(err)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.recording_path, fourcc, fps, (width, height))

        if not self.writer.isOpened():
            # Try alternate fallback codec if mp4v fails
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.writer = cv2.VideoWriter(self.recording_path, fourcc, fps, (width, height))

        if not self.writer.isOpened():
            self.recording_active = False
            self.writer = None
            err = f"Failed to initialize VideoWriter for path: {self.recording_path}"
            print(f"[VideoOutputManager] Error: {err}")
            raise RuntimeError(err)

        self.recording_active = True
        self.frames_recorded = 0
        print(f"[VideoOutputManager] Recording started: {self.recording_path} ({width}x{height} @ {fps} FPS)")
        return self.recording_path

    def stop_recording(self):
        """Stop current video recording and release VideoWriter."""
        if self.writer is not None:
            try:
                self.writer.release()
            except Exception as e:
                print(f"[VideoOutputManager] Warning while releasing VideoWriter: {e}")
            self.writer = None

        was_recording = self.recording_active
        self.recording_active = False
        saved_path = self.recording_path

        if was_recording:
            print(f"[VideoOutputManager] Recording stopped. Total frames saved: {self.frames_recorded} -> {saved_path}")

        return saved_path

    def enable_network_output(self, target_url, output_type="stub"):
        """Enable network broadcast output."""
        if self.network_output is not None:
            self.network_output.close()

        if output_type == "stub":
            self.network_output = NetworkOutputStub(target_url)
            self.network_output.connect()
        else:
            print(f"[VideoOutputManager] Unsupported network output protocol type: {output_type}")

    def disable_network_output(self):
        """Disable network output stream."""
        if self.network_output is not None:
            self.network_output.close()
            self.network_output = None

    def process_output_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Process output frame: calculate output FPS, write to recording file if active,
        and transmit over network output interface if enabled.
        """
        if frame is None or frame.size == 0:
            return frame

        now = time.time()
        dt = now - self._last_frame_time
        self._last_frame_time = now

        if dt > 0:
            inst_fps = 1.0 / dt
            self.output_fps = 0.9 * self.output_fps + 0.1 * inst_fps if self.output_fps > 0 else inst_fps

        # Write to local recording file if recording
        if self.recording_active and self.writer is not None:
            try:
                self.writer.write(frame)
                self.frames_recorded += 1
            except Exception as e:
                print(f"[VideoOutputManager] Error writing frame to recording: {e}")

        # Send to network output if connected
        if self.network_output is not None and self.network_output.is_connected:
            try:
                self.network_output.send_frame(frame)
            except Exception as e:
                print(f"[VideoOutputManager] Error sending frame to network output: {e}")

        return frame

    def get_output_stats(self):
        """Return output statistics dictionary."""
        return {
            "output_fps": round(self.output_fps, 1),
            "recording_active": self.recording_active,
            "recording_path": self.recording_path if self.recording_active else None,
            "frames_recorded": self.frames_recorded,
            "network_active": self.network_output.is_connected if self.network_output else False,
        }

    def close(self):
        """Clean shutdown of output manager."""
        self.stop_recording()
        self.disable_network_output()
        print("[VideoOutputManager] Closed cleanly.")

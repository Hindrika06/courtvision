"""
Application Controller for CourtVision Desktop Control Center.
Decouples GUI events from the core Computer Vision pipeline.
Integrates VideoInputManager, VideoOutputManager, CourtProfileManager, and SessionManager abstractions.
"""
import os
import sys
import time
import json
import cv2
import numpy as np

try:
    import psutil
except ImportError:
    psutil = None

from vision.pipeline import CourtVisionPipeline
from vision.calibration import save_calibration, load_calibration, is_valid_quad
from application.video_input import VideoInputManager, ConnectionState, sanitize_url
from application.video_output import VideoOutputManager
from application.court_profile_manager import CourtProfileManager
from application.session_manager import SessionManager


class AppController:
    """
    Controller managing video input streams, pipeline execution, performance metrics,
    video output/recording, multi-court profiles, and CourtVisionPipeline instances.
    """

    def __init__(self, root_dir="."):
        self.root_dir = root_dir
        self.profile_manager = CourtProfileManager(root_dir=self.root_dir)
        self.session_manager = SessionManager(session_path=os.path.join(self.root_dir, "config/session.json"))

        self.input_manager = VideoInputManager(config_path=os.path.join(self.root_dir, "config/cameras.json"))
        self.output_manager = VideoOutputManager(output_dir=os.path.join(self.root_dir, "output"))

        self.pipeline = None
        self.is_running = False

        # Active settings
        self.quality = "production"
        self.racket_protection = True
        self.model_name = "yolov8n-seg.pt"

        # Load initial session and court profile
        self.active_profile_id = "court_1"
        self.court_config_path = os.path.join(self.root_dir, "config/profiles/court_1/court.json")
        self.ads_config_path = os.path.join(self.root_dir, "config/profiles/court_1/ads.json")

        self.load_active_profile()

    @property
    def is_recording(self):
        return self.output_manager.recording_active

    @property
    def record_filepath(self):
        return self.output_manager.recording_path

    @staticmethod
    def list_available_cameras(max_check=5):
        """Detect available local camera index list."""
        available = []
        for i in range(max_check):
            try:
                temp_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
                if temp_cap.isOpened():
                    ret, _ = temp_cap.read()
                    if ret:
                        available.append(i)
                    temp_cap.release()
            except Exception:
                pass
        if not available:
            available = [0]
        return available

    def load_active_profile(self, profile_id=None):
        """
        Load configuration paths and settings for active court profile.
        """
        if profile_id:
            self.profile_manager.set_active_profile_id(profile_id)

        self.active_profile_id = self.profile_manager.get_active_profile_id()
        p_data, c_path, a_path = self.profile_manager.load_profile(self.active_profile_id)

        self.court_config_path = c_path
        self.ads_config_path = a_path

        settings = p_data.get("settings", {})
        self.quality = settings.get("quality", self.quality)
        self.racket_protection = settings.get("racket_protection", self.racket_protection)

        # Update session file
        self.session_manager.save_session(
            active_profile=self.active_profile_id,
            last_quality=self.quality,
            racket_protection=self.racket_protection
        )

        return p_data

    def switch_profile(self, new_profile_id):
        """
        Safely switch active court profile. Cleanly stops running streams/recorders,
        loads new court profile configuration, and returns profile data.
        """
        if self.is_running:
            self.stop_stream()

        p_data = self.load_active_profile(new_profile_id)
        self.pipeline = None  # Reset pipeline to force reload with new court/ads config
        print(f"[AppController] Switched active court profile to: '{self.active_profile_id}' ({p_data.get('name')})")
        return p_data

    def get_ads_summary(self):
        """Return list of active ad names from active profile's ads.json."""
        if not os.path.exists(self.ads_config_path):
            return []
        try:
            with open(self.ads_config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [ad.get("name", f"ad_{idx}") for idx, ad in enumerate(data.get("ads", []))]
        except Exception:
            return []

    def get_system_stats(self):
        """Return dict of CPU%, RAM MB, RAM% system metrics."""
        stats = {"cpu_percent": 0.0, "ram_mb": 0.0, "ram_percent": 0.0}
        if psutil is not None:
            try:
                proc = psutil.Process(os.getpid())
                stats["cpu_percent"] = psutil.cpu_percent(interval=None)
                mem = proc.memory_info()
                stats["ram_mb"] = mem.rss / (1024.0 * 1024.0)
                stats["ram_percent"] = psutil.virtual_memory().percent
            except Exception:
                pass
        return stats

    def initialize_pipeline(self):
        """Instantiate CourtVisionPipeline using active controller settings and profile paths."""
        imgsz = 640 if self.quality == "production" else 320
        frame_skip = 0 if self.quality == "production" else 1

        self.pipeline = CourtVisionPipeline(
            court_config_path=self.court_config_path,
            ads_config_path=self.ads_config_path,
            model_name=self.model_name,
            conf_thresh=0.25,
            imgsz=imgsz,
            device="cpu",
            frame_skip=frame_skip,
            racket_protection=self.racket_protection
        )
        return self.pipeline

    def start_stream(self, source, source_type=None, name="Camera", quality="production", racket_protection=True, record_path=None, reconnect=True, delay=3.0):
        """
        Open input stream via VideoInputManager and initialize pipeline.
        Supports Webcam, Video File, and RTSP stream sources.
        """
        self.quality = quality
        self.racket_protection = racket_protection

        # Update active profile camera & settings
        p_data, _, _ = self.profile_manager.load_profile(self.active_profile_id)
        p_data["settings"]["quality"] = quality
        p_data["settings"]["racket_protection"] = racket_protection
        self.profile_manager.update_profile(self.active_profile_id, settings_dict=p_data["settings"])

        # Deduce source_type if not explicitly provided
        if source_type is None:
            if isinstance(source, int) or (isinstance(source, str) and source.isdigit()):
                source_type = "webcam"
                source_val = int(source)
            elif isinstance(source, str) and source.lower().startswith("rtsp://"):
                source_type = "rtsp"
                source_val = source
            else:
                source_type = "video"
                source_val = str(source)
        else:
            source_val = source

        # Open input source
        self.input_manager.open_source(
            source_type=source_type,
            source_val=source_val,
            name=name,
            reconnect=reconnect,
            delay=delay
        )

        # Initialize pipeline
        self.initialize_pipeline()

        # Start recording if requested
        if record_path:
            self.output_manager.start_recording(
                output_path=record_path,
                width=self.input_manager.frame_w,
                height=self.input_manager.frame_h
            )

        self.is_running = True

    def process_next_frame(self, debug_mask=False):
        """
        Fetch latest frame from VideoInputManager, process through CourtVisionPipeline,
        pass to VideoOutputManager, and return (output_frame, debug_info, stats).
        """
        if not self.is_running:
            return None, None, self.get_combined_stats()

        raw_frame = self.input_manager.get_latest_frame()
        if raw_frame is None:
            if self.input_manager.state in (ConnectionState.ERROR, ConnectionState.DISCONNECTED):
                return None, None, self.get_combined_stats()
            return None, None, self.get_combined_stats()

        if self.pipeline is None:
            self.initialize_pipeline()

        if debug_mask:
            out_frame, debug_info = self.pipeline.process_frame(raw_frame, return_debug=True)
        else:
            out_frame = self.pipeline.process_frame(raw_frame, return_debug=False)
            debug_info = {}

        if out_frame is None:
            out_frame = raw_frame

        # Send frame to VideoOutputManager
        out_frame = self.output_manager.process_output_frame(out_frame)

        stats = self.get_combined_stats()

        return out_frame, debug_info, stats

    def get_combined_stats(self):
        """Aggregate stream health metrics, system metrics, and pipeline metrics."""
        health = self.input_manager.get_health_stats()
        out_stats = self.output_manager.get_output_stats()
        sys_stats = self.get_system_stats()

        pipeline_fps = self.pipeline.fps if self.pipeline else 0.0
        inference_ms = self.pipeline.inference_time_ms if self.pipeline else 0.0
        tracking_ms = self.pipeline.tracking_time_ms if self.pipeline else 0.0

        return {
            "active_profile_id": self.active_profile_id,
            "fps": round(pipeline_fps, 1),
            "input_fps": round(health.get("input_fps", 0.0), 1),
            "output_fps": out_stats.get("output_fps", 0.0),
            "inference_ms": round(inference_ms, 1),
            "tracking_ms": round(tracking_ms, 1),
            "cpu_percent": sys_stats["cpu_percent"],
            "ram_mb": sys_stats["ram_mb"],
            "frame_w": self.input_manager.frame_w,
            "frame_h": self.input_manager.frame_h,
            "received_frames": health.get("received_frames", 0),
            "processed_frames": health.get("processed_frames", 0),
            "dropped_frames": health.get("dropped_frames", 0),
            "reconnect_count": health.get("reconnect_count", 0),
            "connection_state": health.get("state", ConnectionState.DISCONNECTED),
            "camera_name": health.get("camera_name", "Camera"),
            "sanitized_url": health.get("sanitized_url", ""),
            "recording_active": out_stats.get("recording_active", False),
            "recording_path": out_stats.get("recording_path", None)
        }

    def start_recording(self, record_path=None):
        """Start recording using VideoOutputManager."""
        w = self.input_manager.frame_w or 1280
        h = self.input_manager.frame_h or 720
        return self.output_manager.start_recording(output_path=record_path, width=w, height=h)

    def stop_recording(self):
        """Stop recording using VideoOutputManager."""
        return self.output_manager.stop_recording()

    def stop_stream(self):
        """Cleanly stop video input, recording, network output, and pipeline execution."""
        self.is_running = False
        self.output_manager.stop_recording()
        self.input_manager.close_source()

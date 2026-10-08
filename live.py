"""
CourtVision Live Application.
Supports live camera inputs (webcam) and pre-recorded video files.

Usage:
    Webcam:             python live.py --source 0
    Video file:         python live.py --source input/input.mp4
    Racket Protection:  python live.py --source input/input.mp4 --racket-protection
    Production Mode:    python live.py --source 0 --quality production
    Performance Mode:   python live.py --source 0 --quality performance
    Record Output:      python live.py --source input/input.mp4 --record output/field_test.mp4
    Debug Mask View:    python live.py --source input/input.mp4 --debug-mask
    Performance HUD:    python live.py --source input/input.mp4 --performance
    Calibration:        python live.py --source 0 --calibrate
"""
import argparse
import os
import sys
import cv2
import numpy as np

from vision.pipeline import CourtVisionPipeline
from vision.calibration import run_calibration
from application.video_input import sanitize_url
from application.court_profile_manager import CourtProfileManager


def parse_source(source_str):
    """Convert integer strings ('0', '1') to int for webcam, otherwise return str."""
    if isinstance(source_str, str) and source_str.isdigit():
        return int(source_str)
    return source_str


def main():
    parser = argparse.ArgumentParser(description="CourtVision Virtual Court Advertising Engine")
    parser.add_argument("--profile", default=None, help="Court profile ID (e.g. court_1, court_2)")
    parser.add_argument("--source", default=None, help="Video file path, webcam index, or RTSP URL (e.g. 0, input/input.mp4, rtsp://192.168.1.100:554/stream)")
    parser.add_argument("--court-config", default=None, help="Path to court calibration JSON")
    parser.add_argument("--ads-config", default=None, help="Path to ads configuration JSON")
    parser.add_argument("--quality", choices=["production", "performance"], default=None, help="Preset quality mode (production=highest quality, performance=fast CPU)")
    parser.add_argument("--model", default="yolov8n-seg.pt", help="Segmentation model weights")
    parser.add_argument("--conf", "--confidence", type=float, default=None, help="Person detection confidence threshold")
    parser.add_argument("--inference-size", type=int, default=None, help="Inference resolution width/height")
    parser.add_argument("--device", default="cpu", help="Inference device (cpu, cuda, mps)")
    parser.add_argument("--frame-skip", type=int, default=None, help="Frame skipping factor for detection (0=every frame)")
    
    # Racket / Fine-object protection CLI flags
    parser.add_argument("--racket-protection", "--racket", action="store_true", help="Enable fine-object / racket protection mask")
    parser.add_argument("--racket-conf", type=float, default=0.25, help="Racket detection confidence threshold")
    parser.add_argument("--racket-model", default=None, help="Optional dedicated racket segmentation model weights")

    parser.add_argument("--record", default=None, help="Optional output MP4 file path to record composited output video")
    parser.add_argument("--calibrate", action="store_true", help="Launch interactive court calibration tool")
    parser.add_argument("--debug-mask", action="store_true", help="Display 2x2 debug visualization grid")
    parser.add_argument("--performance", action="store_true", help="Display detailed performance metrics breakdown")
    parser.add_argument("--loop", action="store_true", help="Loop video input when finished")
    parser.add_argument("--no-display", action="store_true", help="Run without showing GUI window (headless/benchmark mode)")

    args = parser.parse_args()

    # Load Court Profile if specified or by default
    profile_mgr = CourtProfileManager()
    target_profile_id = args.profile or profile_mgr.get_active_profile_id()
    try:
        p_data, p_court_path, p_ads_path = profile_mgr.load_profile(target_profile_id)
        print(f"[CourtVision] Loaded Court Profile: '{target_profile_id}' ({p_data.get('name', 'Court')})")
    except Exception as e:
        print(f"[CourtVision] Warning loading profile '{target_profile_id}': {e}")
        p_data, p_court_path, p_ads_path = {}, "config/court.json", "config/ads.json"

    # Resolve paths (explicit CLI args take precedence over profile defaults)
    court_config = args.court_config or p_court_path
    ads_config = args.ads_config or p_ads_path

    # Resolve input source (CLI --source takes precedence, otherwise profile camera source)
    raw_source = args.source if args.source is not None else p_data.get("camera", {}).get("source", 0)
    source = parse_source(raw_source)

    # Resolve quality mode
    quality_mode = args.quality or p_data.get("settings", {}).get("quality", "production")
    racket_protection = args.racket_protection or p_data.get("settings", {}).get("racket_protection", True)

    # Resolve quality preset defaults if specified
    if args.quality == "production":
        imgsz = args.inference_size if args.inference_size is not None else 640
        frame_skip = args.frame_skip if args.frame_skip is not None else 0
        conf_thresh = args.conf if args.conf is not None else 0.25
    elif args.quality == "performance":
        imgsz = args.inference_size if args.inference_size is not None else 320
        frame_skip = args.frame_skip if args.frame_skip is not None else 1
        conf_thresh = args.conf if args.conf is not None else 0.25
    else:
        imgsz = args.inference_size if args.inference_size is not None else 640
        frame_skip = args.frame_skip if args.frame_skip is not None else 0
        conf_thresh = args.conf if args.conf is not None else 0.25

    # 1. Validation checks on source and files
    is_rtsp = isinstance(source, str) and source.lower().startswith("rtsp://")
    if isinstance(source, str) and not is_rtsp and not os.path.exists(source):
        print(f"ERROR: Input video file not found at: {source}")
        print("Please verify the file path and try again.")
        sys.exit(1)

    # Launch calibration if requested or if calibration config is missing
    if args.calibrate or not os.path.exists(court_config):
        print(f"Calibration requested or missing config '{court_config}'. Starting calibration...")
        try:
            success = run_calibration(source, court_config)
            if not success:
                print("Calibration was cancelled or failed. Exiting.")
                sys.exit(1)
        except Exception as e:
            print(f"ERROR during court calibration: {e}")
            sys.exit(1)

    # Initialize Video Capture
    sanitized_src = sanitize_url(str(source))
    print(f"[CourtVision] Opening input source: {sanitized_src}...")
    try:
        cap = cv2.VideoCapture(source)
    except Exception as e:
        print(f"ERROR: Exception while opening input source {sanitized_src}: {e}")
        sys.exit(1)

    if not cap.isOpened():
        print(f"ERROR: Could not open video/camera source: {sanitized_src}")
        print("Please verify the camera is connected or the video path is valid.")
        sys.exit(1)

    # Initialize Pipeline ONCE before loop
    print(f"[CourtVision] Initializing pipeline (court_config={court_config}, quality={quality_mode}, imgsz={imgsz}, frame_skip={frame_skip}, racket_protection={racket_protection})...")
    try:
        pipeline = CourtVisionPipeline(
            court_config_path=court_config,
            ads_config_path=ads_config,
            model_name=args.model,
            conf_thresh=conf_thresh,
            imgsz=imgsz,
            device=args.device,
            frame_skip=frame_skip,
            racket_protection=racket_protection,
            racket_model=args.racket_model,
            racket_conf=args.racket_conf
        )
    except FileNotFoundError as fnf:
        print(f"ERROR: Configuration file missing: {fnf}")
        cap.release()
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Pipeline initialization failed: {e}")
        cap.release()
        sys.exit(1)

    # Initialize Optional Video Recorder
    video_writer = None
    if args.record:
        os.makedirs(os.path.dirname(args.record) or ".", exist_ok=True)
        rec_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
        rec_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
        rec_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(args.record, fourcc, rec_fps, (rec_w, rec_h))
        print(f"[CourtVision] Recording composited output to: {args.record} ({rec_w}x{rec_h} @ {rec_fps:.1f} fps)")

    window_name = "CourtVision"
    if not args.no_display:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    print("[CourtVision] Starting processing loop. Press 'q' or ESC to quit.")

    try:
        while True:
            ret, frame = cap.read()

            if not ret or frame is None or frame.size == 0:
                if args.loop and isinstance(source, str):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    print("[CourtVision] Video stream ended or camera disconnected.")
                    break

            # Process frame through CourtVision pipeline
            need_debug = args.debug_mask
            if need_debug:
                output_frame, debug_info = pipeline.process_frame(frame, return_debug=True)
            else:
                output_frame = pipeline.process_frame(frame, return_debug=False)

            if output_frame is None:
                output_frame = frame

            # Record composited output frame if recording enabled
            if video_writer is not None:
                video_writer.write(output_frame)

            # Render Performance HUD if requested
            if args.performance:
                hud_lines = [
                    "CourtVision Performance",
                    f"FPS: {pipeline.fps:.1f}",
                    f"Inference:   {pipeline.inference_time_ms:.1f} ms",
                    f"Tracking:    {pipeline.tracking_time_ms:.1f} ms",
                    f"Mask Gen:    {pipeline.mask_gen_time_ms:.1f} ms",
                    f"Ad Warping:  {pipeline.ad_warp_time_ms:.1f} ms",
                    f"Compositing: {pipeline.compositing_time_ms:.1f} ms",
                    f"Total Frame: {pipeline.total_frame_time_ms:.1f} ms",
                ]
                # Draw semi-transparent HUD panel
                panel_h = len(hud_lines) * 22 + 15
                panel_w = 260
                sub = output_frame[10:10+panel_h, 10:10+panel_w]
                if sub.shape[0] == panel_h and sub.shape[1] == panel_w:
                    black_rect = np.zeros_like(sub)
                    output_frame[10:10+panel_h, 10:10+panel_w] = cv2.addWeighted(sub, 0.4, black_rect, 0.6, 0)
                
                for idx, line in enumerate(hud_lines):
                    color = (0, 255, 255) if idx == 0 else (0, 255, 0)
                    scale = 0.55 if idx == 0 else 0.48
                    cv2.putText(
                        output_frame,
                        line,
                        (15, 30 + idx * 22),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        scale,
                        color,
                        1,
                        cv2.LINE_AA
                    )
            else:
                # Basic FPS Overlay
                fps_text = f"CourtVision | FPS: {pipeline.fps:.1f}"
                cv2.putText(
                    output_frame,
                    fps_text,
                    (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA
                )

            # Debug Grid Mode (2x2 Display)
            if args.debug_mask and not args.no_display:
                h_f, w_f = frame.shape[:2]
                half_w, half_h = w_f // 2, h_f // 2

                # View 1: Original
                v1 = cv2.resize(frame, (half_w, half_h))
                cv2.putText(v1, "1. Original Frame", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # View 2: Player Protection Mask
                p_mask_vis = (debug_info["player_mask"] * 255).astype(np.uint8)
                v2_color = cv2.cvtColor(p_mask_vis, cv2.COLOR_GRAY2BGR)
                v2 = cv2.resize(v2_color, (half_w, half_h))
                cv2.putText(v2, "2. Combined Protection Mask", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # View 3: Racket Mask or Ad Layer
                r_mask_vis = (debug_info.get("racket_mask", np.zeros((h_f, w_f), dtype=np.uint8)) * 255).astype(np.uint8)
                v3_color = cv2.cvtColor(r_mask_vis, cv2.COLOR_GRAY2BGR)
                if np.any(r_mask_vis):
                    v3 = cv2.resize(v3_color, (half_w, half_h))
                    lbl3 = "3. Racket Mask"
                else:
                    v3 = cv2.resize(debug_info["ad_layer"], (half_w, half_h))
                    lbl3 = "3. Warped Ad Layer"
                cv2.putText(v3, lbl3, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # View 4: Final Output
                v4 = cv2.resize(output_frame, (half_w, half_h))
                cv2.putText(v4, "4. Final Composited Output", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                top_row = np.hstack([v1, v2])
                bottom_row = np.hstack([v3, v4])
                grid = np.vstack([top_row, bottom_row])

                cv2.imshow("CourtVision DEBUG MASK VIEW", grid)
            elif not args.no_display:
                cv2.imshow(window_name, output_frame)

            if not args.no_display:
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), ord('Q'), 27):
                    print("[CourtVision] User quit requested.")
                    break

    except KeyboardInterrupt:
        print("[CourtVision] Interrupted by user.")
    except Exception as e:
        print(f"ERROR: Runtime error during execution: {e}")

    # Graceful cleanup
    cap.release()
    if video_writer is not None:
        video_writer.release()
        print(f"[CourtVision] Recorded output video saved successfully to {args.record}")
    if not args.no_display:
        cv2.destroyAllWindows()
    print("[CourtVision] Processing finished cleanly.")


if __name__ == "__main__":
    main()

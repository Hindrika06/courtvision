"""
CourtVision Desktop Control Center Main Window.
Dark control-room operator interface with non-blocking worker thread,
RTSP / IP Camera controls, Stream Health monitoring, Multi-Court Profiles, and Session Management.
"""
import os
import sys
import time
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk

from application.controller import AppController
from application.video_input import ConnectionState, sanitize_url
from application.version import VERSION, APP_NAME, AI_ENGINE, DESCRIPTION
from application.logger import log_info, log_error
from ui.calibration_wizard import CalibrationWizard


class CourtProfileDialog(tk.Toplevel):
    """Dialog for creating or editing court profiles."""

    def __init__(self, parent, title="New Court Profile", profile_data=None, existing_profiles=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x440")
        self.configure(bg="#25252c")
        self.resizable(False, False)

        self.result = None
        self.profile_data = profile_data or {}
        self.existing_profiles = existing_profiles or []

        self.id_var = tk.StringVar(value=self.profile_data.get("id", ""))
        self.name_var = tk.StringVar(value=self.profile_data.get("name", ""))
        self.desc_var = tk.StringVar(value=self.profile_data.get("description", ""))
        self.quality_var = tk.StringVar(value=self.profile_data.get("settings", {}).get("quality", "production"))
        self.racket_var = tk.BooleanVar(value=self.profile_data.get("settings", {}).get("racket_protection", True))
        self.copy_from_var = tk.StringVar(value="court_1")

        self.is_edit = bool(profile_data)

        self._build_ui()
        self.transient(parent)
        self.grab_set()

    def _build_ui(self):
        pad = {"padx": 15, "pady": 6}

        lbl_title = tk.Label(self, text=self.title(), font=("Segoe UI", 12, "bold"), bg="#25252c", fg="#00e5ff")
        lbl_title.pack(anchor="w", **pad)

        if not self.is_edit:
            tk.Label(self, text="Court Profile ID (e.g. court_2):", bg="#25252c", fg="#ffffff").pack(anchor="w", **pad)
            entry_id = ttk.Entry(self, textvariable=self.id_var)
            entry_id.pack(fill="x", **pad)

        tk.Label(self, text="Court Display Name:", bg="#25252c", fg="#ffffff").pack(anchor="w", **pad)
        entry_name = ttk.Entry(self, textvariable=self.name_var)
        entry_name.pack(fill="x", **pad)

        tk.Label(self, text="Description:", bg="#25252c", fg="#ffffff").pack(anchor="w", **pad)
        entry_desc = ttk.Entry(self, textvariable=self.desc_var)
        entry_desc.pack(fill="x", **pad)

        tk.Label(self, text="Quality Preset:", bg="#25252c", fg="#ffffff").pack(anchor="w", **pad)
        qual_combo = ttk.Combobox(self, textvariable=self.quality_var, values=["production", "performance"], state="readonly")
        qual_combo.pack(fill="x", **pad)

        chk_racket = tk.Checkbutton(
            self, text="Enable Racket Protection", variable=self.racket_var,
            bg="#25252c", fg="#ffffff", selectcolor="#007acc", activebackground="#25252c", activeforeground="#ffffff"
        )
        chk_racket.pack(anchor="w", **pad)

        if not self.is_edit and self.existing_profiles:
            tk.Label(self, text="Copy Initial Config From:", bg="#25252c", fg="#ffffff").pack(anchor="w", **pad)
            copy_combo = ttk.Combobox(self, textvariable=self.copy_from_var, values=[p["id"] for p in self.existing_profiles], state="readonly")
            copy_combo.pack(fill="x", **pad)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=15, padx=15)

        btn_save = ttk.Button(btn_frame, text="SAVE PROFILE", command=self._on_save)
        btn_save.pack(side="right", padx=5)

        btn_cancel = ttk.Button(btn_frame, text="CANCEL", command=self.destroy)
        btn_cancel.pack(side="right")

    def _on_save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Validation Error", "Court Display Name is required.", parent=self)
            return

        if not self.is_edit:
            pid = self.id_var.get().strip()
            if not pid:
                # Auto-generate ID from name
                pid = name.lower().replace(" ", "_")

            self.result = {
                "id": pid,
                "name": name,
                "description": self.desc_var.get().strip(),
                "quality": self.quality_var.get(),
                "racket_protection": self.racket_var.get(),
                "copy_from": self.copy_from_var.get()
            }
        else:
            self.result = {
                "name": name,
                "description": self.desc_var.get().strip(),
                "quality": self.quality_var.get(),
                "racket_protection": self.racket_var.get()
            }

        self.destroy()


class CourtVisionMainWindow:
    """
    Dark control-room style desktop GUI for CourtVision.
    Runs pipeline processing off-main-thread so GUI remains 100% responsive.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("CourtVision Desktop Control Center")
        self.root.geometry("1380x860")
        self.root.configure(bg="#18181c")

        self.controller = AppController()
        self.frame_queue = queue.Queue(maxsize=2)
        self.stop_event = threading.Event()
        self.worker_thread = None

        self.available_cams = self.controller.list_available_cameras()
        self.selected_file_path = None
        self.debug_mask_var = tk.BooleanVar(value=False)
        self.racket_var = tk.BooleanVar(value=self.controller.racket_protection)

        # Profile selection variable
        self.profile_var = tk.StringVar(value=self.controller.active_profile_id)

        # RTSP variables
        self.rtsp_name_var = tk.StringVar(value="Court Camera 1")
        self.rtsp_url_var = tk.StringVar(value="rtsp://192.168.1.100:554/stream1")
        self.rtsp_reconnect_var = tk.BooleanVar(value=True)
        self.rtsp_delay_var = tk.StringVar(value="3")

        self._setup_styles()
        self._build_ui()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        bg_dark = "#18181c"
        card_bg = "#25252c"
        accent_blue = "#007acc"
        text_light = "#f0f0f0"

        style.configure("TFrame", background=bg_dark)
        style.configure("Card.TFrame", background=card_bg, relief="flat", borderwidth=1)
        style.configure("TLabelframe", background=card_bg, foreground="#ffffff", font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background=card_bg, foreground="#00e5ff", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background=card_bg, foreground=text_light, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=bg_dark, foreground="#ffffff", font=("Segoe UI", 16, "bold"))
        style.configure("Status.TLabel", background="#121214", foreground="#00ff66", font=("Consolas", 9, "bold"))

        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=5)
        style.map("TButton", background=[("active", "#005999"), ("!disabled", accent_blue)], foreground=[("!disabled", "#ffffff")])
        style.configure("Stop.TButton", font=("Segoe UI", 9, "bold"), padding=5)
        style.map("Stop.TButton", background=[("active", "#a00000"), ("!disabled", "#cc0000")], foreground=[("!disabled", "#ffffff")])

    def _build_ui(self):
        # Header Bar
        header_frame = ttk.Frame(self.root, style="TFrame", padding=(15, 10))
        header_frame.pack(fill="x")

        title_lbl = ttk.Label(header_frame, text="CourtVision 🎾 Control Center", style="Header.TLabel")
        title_lbl.pack(side="left")

        self.status_badge = tk.Label(
            header_frame, text="● DISCONNECTED", font=("Segoe UI", 10, "bold"),
            bg="#444444", fg="#ffffff", padx=12, pady=4
        )
        self.status_badge.pack(side="right")

        # Main Layout Container (Video Preview left, Sidebar right)
        main_container = ttk.Frame(self.root, style="TFrame")
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Video Preview Canvas Left Box
        preview_frame = ttk.Frame(main_container, style="Card.TFrame")
        preview_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.preview_canvas = tk.Label(preview_frame, bg="#0d0d0f", text="Camera Preview (Press Start to Begin)")
        self.preview_canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # Camera position fixed warning banner
        warn_lbl = tk.Label(
            preview_frame,
            text="⚠️ Note: CourtVision requires a fixed camera position per court. Recalibrate if camera moves.",
            bg="#2a2010", fg="#ffbb33", font=("Segoe UI", 8, "italic"), pady=2
        )
        warn_lbl.pack(fill="x", side="bottom")

        # Sidebar Panel Right (380px wide)
        panel_container = ttk.Frame(main_container, style="Card.TFrame", width=380)
        panel_container.pack(side="right", fill="y")
        panel_container.pack_propagate(False)

        panel_canvas = tk.Canvas(panel_container, bg="#25252c", highlightthickness=0)
        scrollbar = ttk.Scrollbar(panel_container, orient="vertical", command=panel_canvas.yview)
        panel_frame = ttk.Frame(panel_canvas, style="Card.TFrame")

        panel_frame.bind(
            "<Configure>",
            lambda e: panel_canvas.configure(scrollregion=panel_canvas.bbox("all"))
        )
        panel_canvas.create_window((0, 0), window=panel_frame, anchor="nw", width=360)
        panel_canvas.configure(yscrollcommand=scrollbar.set)

        panel_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- GROUP 1: COURT PROFILE SELECTION ---
        profile_group = ttk.LabelFrame(panel_frame, text=" Court Profile ", padding=8)
        profile_group.pack(fill="x", padx=8, pady=6)

        ttk.Label(profile_group, text="Active Court:").pack(anchor="w")

        prof_select_frame = ttk.Frame(profile_group)
        prof_select_frame.pack(fill="x", pady=(2, 6))

        self.profile_combo = ttk.Combobox(prof_select_frame, state="readonly")
        self.profile_combo.pack(side="left", fill="x", expand=True)
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_combo_select)

        self._refresh_profile_list()

        prof_btns_frame = ttk.Frame(profile_group)
        prof_btns_frame.pack(fill="x", pady=2)

        btn_new_prof = ttk.Button(prof_btns_frame, text="+ NEW", width=7, command=self._on_new_profile)
        btn_new_prof.pack(side="left", padx=(0, 4))

        btn_edit_prof = ttk.Button(prof_btns_frame, text="EDIT", width=7, command=self._on_edit_profile)
        btn_edit_prof.pack(side="left", padx=4)

        btn_del_prof = ttk.Button(prof_btns_frame, text="DELETE", width=7, command=self._on_delete_profile)
        btn_del_prof.pack(side="left", padx=4)

        # Profile details summary card
        self.lbl_prof_info = ttk.Label(profile_group, text="", font=("Consolas", 8), foreground="#00e5ff")
        self.lbl_prof_info.pack(anchor="w", pady=(4, 0))

        # --- GROUP 2: INPUT SOURCE SELECTION ---
        src_group = ttk.LabelFrame(panel_frame, text=" Input Source ", padding=8)
        src_group.pack(fill="x", padx=8, pady=6)

        self.src_type_var = tk.StringVar(value="webcam")

        radio_frame = ttk.Frame(src_group)
        radio_frame.pack(fill="x", pady=2)

        rb_webcam = tk.Radiobutton(
            radio_frame, text="Webcam", variable=self.src_type_var, value="webcam",
            bg="#25252c", fg="#ffffff", selectcolor="#007acc", activebackground="#25252c", activeforeground="#ffffff",
            command=self._on_source_type_change
        )
        rb_webcam.pack(side="left", padx=2)

        rb_video = tk.Radiobutton(
            radio_frame, text="Video File", variable=self.src_type_var, value="video",
            bg="#25252c", fg="#ffffff", selectcolor="#007acc", activebackground="#25252c", activeforeground="#ffffff",
            command=self._on_source_type_change
        )
        rb_video.pack(side="left", padx=2)

        rb_rtsp = tk.Radiobutton(
            radio_frame, text="RTSP Stream", variable=self.src_type_var, value="rtsp",
            bg="#25252c", fg="#ffffff", selectcolor="#007acc", activebackground="#25252c", activeforeground="#ffffff",
            command=self._on_source_type_change
        )
        rb_rtsp.pack(side="left", padx=2)

        # Webcam Config Controls
        self.webcam_frame = ttk.Frame(src_group)
        cam_options = [f"Webcam {i}" for i in self.available_cams]
        self.cam_combo = ttk.Combobox(self.webcam_frame, values=cam_options, state="readonly")
        if cam_options:
            self.cam_combo.current(0)
        self.cam_combo.pack(fill="x", pady=4)

        # Video Config Controls
        self.video_frame = ttk.Frame(src_group)
        self.file_lbl = ttk.Label(self.video_frame, text="input/input.mp4", font=("Segoe UI", 8))
        self.file_lbl.pack(side="left", fill="x", expand=True)
        btn_browse = ttk.Button(self.video_frame, text="Browse", width=7, command=self._on_browse_file)
        btn_browse.pack(side="right")

        # RTSP Config Controls
        self.rtsp_frame = ttk.Frame(src_group)
        profiles = self.controller.input_manager.camera_profiles
        profile_names = [p.get("name", "Camera") for p in profiles]
        if profile_names:
            ttk.Label(self.rtsp_frame, text="Saved Profile:").pack(anchor="w")
            self.profile_cam_combo = ttk.Combobox(self.rtsp_frame, values=profile_names, state="readonly")
            self.profile_cam_combo.current(0)
            self.profile_cam_combo.pack(fill="x", pady=(2, 4))
            self.profile_cam_combo.bind("<<ComboboxSelected>>", self._on_camera_profile_select)

        ttk.Label(self.rtsp_frame, text="Camera Name:").pack(anchor="w")
        entry_name = ttk.Entry(self.rtsp_frame, textvariable=self.rtsp_name_var)
        entry_name.pack(fill="x", pady=(0, 4))

        ttk.Label(self.rtsp_frame, text="RTSP URL:").pack(anchor="w")
        entry_url = ttk.Entry(self.rtsp_frame, textvariable=self.rtsp_url_var)
        entry_url.pack(fill="x", pady=(0, 4))

        rec_opts_frame = ttk.Frame(self.rtsp_frame)
        rec_opts_frame.pack(fill="x", pady=2)
        chk_rec = tk.Checkbutton(
            rec_opts_frame, text="Auto Reconnect", variable=self.rtsp_reconnect_var,
            bg="#25252c", fg="#ffffff", selectcolor="#007acc", activebackground="#25252c", activeforeground="#ffffff"
        )
        chk_rec.pack(side="left")

        ttk.Label(rec_opts_frame, text="Delay(s):").pack(side="left", padx=(10, 2))
        entry_delay = ttk.Entry(rec_opts_frame, textvariable=self.rtsp_delay_var, width=4)
        entry_delay.pack(side="left")

        self._on_source_type_change()

        # --- GROUP 3: STREAM HEALTH METRICS ---
        health_group = ttk.LabelFrame(panel_frame, text=" Stream Health ", padding=8)
        health_group.pack(fill="x", padx=8, pady=6)

        self.lbl_health_status = ttk.Label(health_group, text="Status: DISCONNECTED", font=("Segoe UI", 9, "bold"), foreground="#888888")
        self.lbl_health_status.pack(anchor="w", pady=1)

        self.lbl_health_fps = ttk.Label(health_group, text="Input FPS: 0.0  |  Process: 0.0  |  Output: 0.0", font=("Consolas", 8))
        self.lbl_health_fps.pack(anchor="w", pady=1)

        self.lbl_health_res = ttk.Label(health_group, text="Resolution: N/A", font=("Consolas", 8))
        self.lbl_health_res.pack(anchor="w", pady=1)

        self.lbl_health_counts = ttk.Label(health_group, text="Recv: 0  |  Processed: 0  |  Dropped: 0", font=("Consolas", 8))
        self.lbl_health_counts.pack(anchor="w", pady=1)

        self.lbl_health_reconnects = ttk.Label(health_group, text="Reconnect Count: 0", font=("Consolas", 8))
        self.lbl_health_reconnects.pack(anchor="w", pady=1)

        # --- GROUP 4: PIPELINE SETTINGS ---
        qual_group = ttk.LabelFrame(panel_frame, text=" Pipeline Settings ", padding=8)
        qual_group.pack(fill="x", padx=8, pady=6)

        ttk.Label(qual_group, text="Quality Mode:").pack(anchor="w")
        self.qual_combo = ttk.Combobox(qual_group, values=["Production (640, Skip 0)", "Performance (320, Skip 1)"], state="readonly")
        self.qual_combo.current(0 if self.controller.quality == "production" else 1)
        self.qual_combo.pack(fill="x", pady=(2, 6))

        chk_racket = tk.Checkbutton(
            qual_group, text="Enable Racket Protection", variable=self.racket_var,
            bg="#25252c", fg="#ffffff", selectcolor="#007acc", activebackground="#25252c", activeforeground="#ffffff"
        )
        chk_racket.pack(anchor="w")

        chk_debug = tk.Checkbutton(
            qual_group, text="Debug Mask Grid View", variable=self.debug_mask_var,
            bg="#25252c", fg="#ffffff", selectcolor="#007acc", activebackground="#25252c", activeforeground="#ffffff"
        )
        chk_debug.pack(anchor="w")

        # --- GROUP 5: ACTIVE ADVERTISEMENTS ---
        ads_group = ttk.LabelFrame(panel_frame, text=" Active Advertisements ", padding=8)
        ads_group.pack(fill="x", padx=8, pady=6)

        self.lbl_ads = ttk.Label(ads_group, text="", font=("Consolas", 8), foreground="#00e5ff")
        self.lbl_ads.pack(anchor="w")
        self._update_ads_summary()

        # --- GROUP 6: ACTION BUTTONS ---
        btn_group = ttk.Frame(panel_frame)
        btn_group.pack(fill="x", padx=8, pady=10)

        self.btn_start = ttk.Button(btn_group, text="▶ CONNECT & START STREAM", command=self.start_stream)
        self.btn_start.pack(fill="x", pady=3)

        self.btn_stop = ttk.Button(btn_group, text="⏹ DISCONNECT & STOP STREAM", style="Stop.TButton", command=self.stop_stream)
        self.btn_stop.pack(fill="x", pady=3)

        self.btn_record = ttk.Button(btn_group, text="⏺ RECORD VIDEO", command=self.toggle_record)
        self.btn_record.pack(fill="x", pady=3)

        btn_calib = ttk.Button(btn_group, text="⚙ CALIBRATE COURT", command=self.open_calibration_wizard)
        btn_calib.pack(fill="x", pady=3)

        btn_about = ttk.Button(btn_group, text="ℹ ABOUT COURTVISION", command=self.show_about_dialog)
        btn_about.pack(fill="x", pady=3)

        # Status Footer Bar
        status_bar = ttk.Frame(self.root, style="TFrame", padding=(15, 6))
        status_bar.pack(fill="x", side="bottom")

        self.lbl_status = ttk.Label(
            status_bar,
            text=f"Court: {self.controller.active_profile_id} | FPS: 0.0 | CPU: 0% | RAM: 0MB | Res: N/A | DISCONNECTED",
            style="Status.TLabel"
        )
        self.lbl_status.pack(side="left")

        # Check queue loop
        self.root.after(20, self._process_queue_loop)

    def _refresh_profile_list(self):
        profiles = self.controller.profile_manager.list_profiles()
        values = [f"{p['name']} ({p['id']})" for p in profiles]
        self.profile_combo.config(values=values)

        active_id = self.controller.active_profile_id
        for idx, p in enumerate(profiles):
            if p["id"] == active_id:
                self.profile_combo.current(idx)
                break

        self._update_profile_info_card()

    def _update_profile_info_card(self):
        p_id = self.controller.active_profile_id
        p_data, c_path, a_path = self.controller.profile_manager.load_profile(p_id)

        calib_ok = "✓ Configured" if os.path.exists(c_path) else "❌ Missing"
        ads = self.controller.get_ads_summary()
        ads_count_str = f"{len(ads)} Active"

        info_text = (
            f"Court: {p_data.get('name', p_id)}\n"
            f"Camera: {p_data.get('camera', {}).get('name', 'Camera')}\n"
            f"Calibration: {calib_ok}\n"
            f"Ads: {ads_count_str}"
        )
        if hasattr(self, "lbl_prof_info"):
            self.lbl_prof_info.config(text=info_text)

    def _update_ads_summary(self):
        active_ads = self.controller.get_ads_summary()
        ads_text = "\n".join([f"• {ad}" for ad in active_ads]) if active_ads else "No ads loaded"
        if hasattr(self, "lbl_ads"):
            self.lbl_ads.config(text=ads_text)

    def _on_profile_combo_select(self, event=None):
        sel_text = self.profile_combo.get()
        if "(" in sel_text and ")" in sel_text:
            target_id = sel_text.split("(")[-1].replace(")", "").strip()
        else:
            target_id = sel_text

        if target_id == self.controller.active_profile_id:
            return

        # Check recording safety confirmation
        if self.controller.is_recording:
            confirm = messagebox.askyesno(
                "Recording Active",
                "Recording is currently active.\nSwitching court profiles will stop the current recording.\nDo you wish to proceed?",
                icon="warning"
            )
            if not confirm:
                # Revert combo selection
                self._refresh_profile_list()
                return

        # Switch court profile safely
        self.stop_stream()
        self.controller.switch_profile(target_id)

        # Update GUI controls for newly loaded profile
        self.racket_var.set(self.controller.racket_protection)
        self.qual_combo.current(0 if self.controller.quality == "production" else 1)
        self._refresh_profile_list()
        self._update_ads_summary()
        messagebox.showinfo("Court Switched", f"Active court profile switched to:\n{sel_text}")

    def _on_new_profile(self):
        profiles = self.controller.profile_manager.list_profiles()
        dlg = CourtProfileDialog(self.root, title="Create New Court Profile", existing_profiles=profiles)
        self.root.wait_window(dlg)

        if dlg.result:
            res = dlg.result
            try:
                new_id = self.controller.profile_manager.create_profile(
                    profile_id=res["id"],
                    name=res["name"],
                    description=res["description"],
                    settings_dict={"quality": res["quality"], "racket_protection": res["racket_protection"]},
                    copy_from_id=res.get("copy_from")
                )
                self.controller.switch_profile(new_id)
                self._refresh_profile_list()
                self._update_ads_summary()
                messagebox.showinfo("Court Created", f"Successfully created and activated court profile:\n'{res['name']}' ({new_id})")
            except Exception as e:
                messagebox.showerror("Profile Creation Error", str(e))

    def _on_edit_profile(self):
        p_id = self.controller.active_profile_id
        p_data, _, _ = self.controller.profile_manager.load_profile(p_id)
        dlg = CourtProfileDialog(self.root, title=f"Edit Profile: {p_data.get('name')}", profile_data=p_data)
        self.root.wait_window(dlg)

        if dlg.result:
            res = dlg.result
            try:
                self.controller.profile_manager.update_profile(
                    profile_id=p_id,
                    name=res["name"],
                    description=res["description"],
                    settings_dict={"quality": res["quality"], "racket_protection": res["racket_protection"]}
                )
                self.controller.quality = res["quality"]
                self.controller.racket_protection = res["racket_protection"]
                self._refresh_profile_list()
                messagebox.showinfo("Profile Updated", f"Profile '{res['name']}' updated successfully.")
            except Exception as e:
                messagebox.showerror("Profile Update Error", str(e))

    def _on_delete_profile(self):
        p_id = self.controller.active_profile_id
        p_data, _, _ = self.controller.profile_manager.load_profile(p_id)
        name = p_data.get("name", p_id)

        confirm = messagebox.askyesno(
            "Delete Court Profile",
            f"Are you sure you want to delete court profile '{name}' ({p_id})?\n\n"
            f"Note: This removes the court profile configuration file.\n"
            f"It does NOT delete advertisement image files, camera hardware, or global application files.",
            icon="warning"
        )
        if confirm:
            try:
                if self.controller.is_running:
                    self.stop_stream()
                next_id = self.controller.profile_manager.delete_profile(p_id)
                self.controller.switch_profile(next_id)
                self._refresh_profile_list()
                self._update_ads_summary()
                messagebox.showinfo("Profile Deleted", f"Profile '{name}' deleted. Switched active court to '{next_id}'.")
            except Exception as e:
                messagebox.showerror("Delete Error", str(e))

    def _on_source_type_change(self):
        st = self.src_type_var.get()
        self.webcam_frame.pack_forget()
        self.video_frame.pack_forget()
        self.rtsp_frame.pack_forget()

        if st == "webcam":
            self.webcam_frame.pack(fill="x", pady=4)
        elif st == "video":
            self.video_frame.pack(fill="x", pady=4)
        elif st == "rtsp":
            self.rtsp_frame.pack(fill="x", pady=4)

    def _on_camera_profile_select(self, event=None):
        idx = self.profile_cam_combo.current()
        profiles = self.controller.input_manager.camera_profiles
        if 0 <= idx < len(profiles):
            p = profiles[idx]
            self.rtsp_name_var.set(p.get("name", "Camera"))
            self.rtsp_url_var.set(p.get("url", ""))
            self.rtsp_reconnect_var.set(p.get("reconnect", True))
            self.rtsp_delay_var.set(str(p.get("reconnect_delay", 3)))

    def _on_browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv"), ("All Files", "*.*")]
        )
        if file_path:
            self.selected_file_path = file_path
            self.file_lbl.config(text=os.path.basename(file_path))
            self.src_type_var.set("video")
            self._on_source_type_change()

    def open_calibration_wizard(self):
        source_val, _, _ = self._get_selected_source_params()
        was_running = self.controller.is_running
        if was_running:
            self.stop_stream()

        # Save calibration directly to active profile's court.json
        wizard = CalibrationWizard(source=source_val, court_config_path=self.controller.court_config_path)
        success = wizard.run()
        if success:
            self._update_profile_info_card()
            messagebox.showinfo("CourtVision", f"Court calibration saved successfully to active profile '{self.controller.active_profile_id}' ({self.controller.court_config_path})!")

        if was_running:
            self.start_stream()

    def _get_selected_source_params(self):
        st = self.src_type_var.get()
        if st == "video":
            source_val = self.selected_file_path or "input/input.mp4"
            name = f"Video ({os.path.basename(source_val)})"
        elif st == "rtsp":
            source_val = self.rtsp_url_var.get().strip()
            name = self.rtsp_name_var.get().strip() or "RTSP Camera"
        else:
            sel = self.cam_combo.get()
            source_val = int(sel.replace("Webcam ", "")) if sel and "Webcam " in sel else 0
            name = f"Webcam {source_val}"
        return source_val, st, name

    def start_stream(self):
        source_val, src_type, name = self._get_selected_source_params()
        quality = "production" if "Production" in self.qual_combo.get() else "performance"
        racket = self.racket_var.get()
        reconnect = self.rtsp_reconnect_var.get()
        try:
            delay = float(self.rtsp_delay_var.get())
        except ValueError:
            delay = 3.0

        try:
            self.controller.start_stream(
                source=source_val,
                source_type=src_type,
                name=name,
                quality=quality,
                racket_protection=racket,
                reconnect=reconnect,
                delay=delay
            )
            self.stop_event.clear()
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()

            sanitized = sanitize_url(str(source_val))
            self.status_badge.config(text="● CONNECTED", bg="#00aa00", fg="#ffffff")
            print(f"[UI] Stream started: court={self.controller.active_profile_id}, source={sanitized}, type={src_type}")
        except Exception as e:
            messagebox.showerror("CourtVision Error", f"Could not connect to input source:\n{e}")
            self.status_badge.config(text="● ERROR", bg="#cc0000", fg="#ffffff")

    def toggle_record(self):
        if not self.controller.is_running:
            messagebox.showwarning("CourtVision", "Please start live stream before recording.")
            return

        if not self.controller.is_recording:
            try:
                rec_path = self.controller.start_recording()
                self.status_badge.config(text="● REC ⏺", bg="#cc0000", fg="#ffffff")
                self.btn_record.config(text="⏹ STOP RECORDING")
                messagebox.showinfo("CourtVision", f"Recording started:\n{rec_path}")
            except Exception as e:
                messagebox.showerror("CourtVision Error", f"Unable to start recording:\n{e}")
        else:
            saved_path = self.controller.stop_recording()
            self.btn_record.config(text="⏺ RECORD VIDEO")
            self.status_badge.config(text="● STREAMING", bg="#00aa00", fg="#ffffff")
            messagebox.showinfo("CourtVision", f"Recording stopped and saved to:\n{saved_path}")

    def stop_stream(self):
        self.stop_event.set()
        self.controller.stop_stream()
        self.status_badge.config(text="● DISCONNECTED", bg="#444444", fg="#ffffff")
        self.preview_canvas.config(image="", text="Camera Preview (Press Start to Begin)")

    def _worker_loop(self):
        while not self.stop_event.is_set() and self.controller.is_running:
            out_frame, debug_info, stats = self.controller.process_next_frame(debug_mask=self.debug_mask_var.get())
            if out_frame is None and stats.get("connection_state") in (ConnectionState.ERROR, ConnectionState.DISCONNECTED):
                time.sleep(0.05)
                continue

            if out_frame is not None:
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                self.frame_queue.put((out_frame, debug_info, stats))
            time.sleep(0.005)

    def _process_queue_loop(self):
        try:
            while not self.frame_queue.empty():
                out_frame, debug_info, stats = self.frame_queue.get_nowait()

                # Update Preview Image
                if self.debug_mask_var.get() and debug_info:
                    h_f, w_f = out_frame.shape[:2]
                    half_w, half_h = w_f // 2, h_f // 2
                    v1 = cv2.resize(debug_info.get("original", out_frame), (half_w, half_h))
                    p_mask = (debug_info.get("player_mask", np.zeros((h_f, w_f))) * 255).astype(np.uint8)
                    v2 = cv2.resize(cv2.cvtColor(p_mask, cv2.COLOR_GRAY2BGR), (half_w, half_h))
                    v3 = cv2.resize(debug_info.get("ad_layer", out_frame), (half_w, half_h))
                    v4 = cv2.resize(out_frame, (half_w, half_h))
                    display_frame = np.vstack([np.hstack([v1, v2]), np.hstack([v3, v4])])
                else:
                    display_frame = out_frame

                rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(rgb)

                canvas_w = max(400, self.preview_canvas.winfo_width())
                canvas_h = max(300, self.preview_canvas.winfo_height())
                img_pil.thumbnail((canvas_w, canvas_h), Image.Resampling.BILINEAR)

                img_tk = ImageTk.PhotoImage(image=img_pil)
                self.preview_canvas.config(image=img_tk, text="")
                self.preview_canvas.image = img_tk

                state = stats.get("connection_state", ConnectionState.DISCONNECTED)
                if state == ConnectionState.STREAMING:
                    self.status_badge.config(text="● STREAMING", bg="#00aa00")
                elif state == ConnectionState.RECONNECTING:
                    self.status_badge.config(text="● RECONNECTING...", bg="#ffaa00")
                elif state == ConnectionState.CONNECTED:
                    self.status_badge.config(text="● CONNECTED", bg="#00aa00")
                elif state == ConnectionState.ERROR:
                    self.status_badge.config(text="● ERROR", bg="#cc0000")

                self.lbl_health_status.config(
                    text=f"Status: {state} ({stats.get('camera_name', 'Camera')})",
                    foreground="#00ff66" if state == ConnectionState.STREAMING else "#ffaa00"
                )
                self.lbl_health_fps.config(
                    text=f"Input FPS: {stats.get('input_fps', 0.0):.1f} | Proc: {stats.get('fps', 0.0):.1f} | Out: {stats.get('output_fps', 0.0):.1f}"
                )
                self.lbl_health_res.config(
                    text=f"Resolution: {stats.get('frame_w', 0)}x{stats.get('frame_h', 0)}"
                )
                self.lbl_health_counts.config(
                    text=f"Recv: {stats.get('received_frames', 0)} | Proc: {stats.get('processed_frames', 0)} | Drop: {stats.get('dropped_frames', 0)}"
                )
                self.lbl_health_reconnects.config(
                    text=f"Reconnect Count: {stats.get('reconnect_count', 0)}"
                )

                status_str = (
                    f"Court: {stats.get('active_profile_id', 'court_1')} | "
                    f"FPS {stats.get('fps', 0.0):.1f} | "
                    f"CPU {stats.get('cpu_percent', 0.0):.1f}% | "
                    f"RAM {stats.get('ram_mb', 0.0):.0f}MB | "
                    f"{stats.get('frame_w', 0)}x{stats.get('frame_h', 0)} | "
                    f"{state}"
                )
                self.lbl_status.config(text=status_str)

        except Exception as e:
            pass

        if not self.stop_event.is_set():
            self.root.after(20, self._process_queue_loop)

    def show_about_dialog(self):
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} v{VERSION}\n\n"
            f"{DESCRIPTION}\n\n"
            f"AI Engine:\n"
            f"• {AI_ENGINE}\n\n"
            f"Capabilities:\n"
            f"• Real-Time Court Advertisement Rendering\n"
            f"• Pixel-Level Player Protection (No Blur)\n"
            f"• Racket & Fine-Object Occlusion Masking\n"
            f"• RTSP / IP Camera Support & Auto-Reconnect\n"
            f"• Multi-Court Profiles & Session Persistence\n"
            f"• Timestamped MP4 Broadcast Recording\n\n"
            f"© 2026 CourtVision Engineering Team"
        )

    def on_close(self):
        self.stop_stream()
        self.root.destroy()

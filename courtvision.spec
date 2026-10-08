# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification for CourtVision Standalone Executable.
Bundles PyTorch, OpenCV, Ultralytics, and application assets into CourtVision.exe.
"""

import sys
import os

block_cipher = None

added_files = [
    ('models/yolov8n-seg.pt', 'models'),
    ('config/court.json', 'config'),
    ('config/ads.json', 'config'),
    ('config/cameras.json', 'config'),
    ('ads/*', 'ads'),
]

hidden_imports = [
    'cv2',
    'numpy',
    'torch',
    'torchvision',
    'ultralytics',
    'PIL',
    'PIL.ImageTk',
    'psutil',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'application.controller',
    'application.court_profile_manager',
    'application.session_manager',
    'application.video_input',
    'application.video_output',
    'application.paths',
    'application.logger',
    'application.version',
    'vision.pipeline',
    'vision.calibration',
    'vision.homography',
    'vision.compositor',
    'vision.player_detector',
    'vision.player_tracker',
    'vision.player_mask',
    'vision.fine_object_detector',
    'ui.main_window',
    'ui.calibration_wizard',
]

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CourtVision',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed GUI without console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CourtVision',
)

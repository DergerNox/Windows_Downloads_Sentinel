# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Windows Downloads Sentinel
"""

import sys
import os

block_cipher = None

# Get the directory containing this spec file
spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
src_dir = os.path.join(spec_dir, 'src')

a = Analysis(
    ['src/main.py'],
    pathex=[spec_dir, src_dir],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('config', 'config'),
        # Include all source modules as data to ensure they're found
        ('src/core', 'core'),
        ('src/ai', 'ai'),
        ('src/ui', 'ui'),
    ],
    hiddenimports=[
        'pystray._win32',
        'PIL._tkinter_finder',
        'customtkinter',
        'google.genai',
        'watchdog.observers',
        'watchdog.events',
        # Explicitly list our modules
        'core',
        'core.gaming_detector',
        'core.watcher',
        'core.task_dispatcher',
        'core.sentinel_worker',
        'ai',
        'ai.workflow_engine',
        'ai.rule_engine',
        'ai.privacy_filter',
        'ai.gemini_client',
        'ai.local_client',
        'ui',
        'ui.tray',
        'ui.settings',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DownloadsSentinel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

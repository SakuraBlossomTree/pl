#!/usr/bin/env python3
"""
Lofi Music Player - A TUI music player with YouTube search and local library support.

Usage:
    python main.py

Requirements:
    - Python 3.8+
    - mpv (must be installed on system)
    - See requirements.txt for Python dependencies

Features:
    - Play music from local library (~/Music)
    - Search and stream from YouTube
    - Fuzzy search across all sources
    - Queue management
    - Download YouTube tracks
    - Rich TUI interface
"""

import sys
import os
from pathlib import Path

# CRITICAL: Set up mpv DLL path BEFORE any imports that use mpv
# This must happen before importing tui.app or player modules
if sys.platform == "win32":
    # Check for libmpv-2.dll in various locations
    possible_paths = [
        Path(__file__).parent / "lib",  # Local lib folder
        Path(r"C:\ProgramData\chocolatey\lib\mpvio.install\tools"),
        Path(r"C:\Program Files\mpv"),
        Path(r"C:\Program Files (x86)\mpv"),
    ]
    
    for mpv_path in possible_paths:
        dll_file = mpv_path / "libmpv-2.dll"
        if dll_file.exists():
            # Add to PATH before importing mpv
            mpv_path_str = str(mpv_path.absolute())
            if mpv_path_str not in os.environ["PATH"]:
                os.environ["PATH"] = mpv_path_str + os.pathsep + os.environ["PATH"]
            print(f"[OK] Found libmpv-2.dll at: {mpv_path}")
            break
    else:
        # Check if PATH already contains it somewhere
        path_dirs = os.environ["PATH"].split(os.pathsep)
        found = False
        for path_dir in path_dirs:
            if (Path(path_dir) / "libmpv-2.dll").exists():
                found = True
                print(f"[OK] libmpv-2.dll found in PATH: {path_dir}")
                break
        
        if not found:
            print("\n" + "="*70)
            print("ERROR: libmpv-2.dll not found!")
            print("="*70)
            print("\nPlease download libmpv-2.dll and place it in the 'lib/' folder.")
            print("Run: python setup_mpv.py for instructions.")
            print("="*70 + "\n")
            sys.exit(1)

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
import logging
from pathlib import Path
log_file = Path(__file__).parent / "lofi_player.log"
logging.basicConfig(
    filename=str(log_file),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("Starting Lofi Music Player")

from tui.app import main

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("Fatal error:")
        raise

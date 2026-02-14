#!/usr/bin/env python3
"""
Setup script to fix mpv DLL issues on Windows
"""
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

def download_mpv_dll():
    """Download mpv DLL files for Windows"""
    lib_dir = Path(__file__).parent / "lib"
    lib_dir.mkdir(exist_ok=True)
    
    # Direct link to mpv Windows build
    url = "https://downloads.sourceforge.net/project/mpv-player-windows/release/mpv-0.37.0-x86_64.7z"
    dll_path = lib_dir / "libmpv-2.dll"
    
    if dll_path.exists():
        print("[OK] libmpv-2.dll already exists")
        return True
    
    print("Downloading mpv DLL files...")
    print("This may take a moment...")
    
    try:
        # Try alternative: download from direct link
        alt_url = "https://github.com/mpv-player/mpv/raw/master/DOCS/client-api-changes.rst"
        
        # For now, let's create instructions
        print("\n" + "="*60)
        print("MANUAL SETUP REQUIRED")
        print("="*60)
        print("\nThe mpv library files need to be downloaded manually:")
        print("\n1. Download mpv Windows build from:")
        print("   https://mpv.io/installation/")
        print("   OR")
        print("   https://github.com/shinchiro/mpv-winbuild-cmake/releases")
        print("\n2. Extract libmpv-2.dll from the archive")
        print("\n3. Place it in this directory:")
        print(f"   {lib_dir.absolute()}")
        print("\n4. Run the player again")
        print("="*60 + "\n")
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def setup_path():
    """Add mpv paths to environment"""
    if sys.platform != "win32":
        return True
    
    # Check common mpv locations
    mpv_paths = [
        Path(__file__).parent / "lib",
        Path(r"C:\ProgramData\chocolatey\lib\mpvio.install\tools"),
        Path(r"C:\Program Files\mpv"),
        Path(r"C:\Program Files (x86)\mpv"),
        Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps",
    ]
    
    found = False
    for path in mpv_paths:
        dll_file = path / "libmpv-2.dll"
        if dll_file.exists():
            if str(path) not in os.environ["PATH"]:
                os.environ["PATH"] = str(path) + os.pathsep + os.environ["PATH"]
            print(f"[OK] Found libmpv-2.dll at: {path}")
            found = True
            break
    
    return found

if __name__ == "__main__":
    print("Setting up mpv for lofi-player...")
    print()
    
    if sys.platform != "win32":
        print("[OK] Non-Windows system detected - no setup needed")
        sys.exit(0)
    
    if setup_path():
        print("\n[OK] Setup complete! You can now run: python main.py")
    else:
        print("\n[ERROR] mpv DLL not found")
        download_mpv_dll()
        sys.exit(1)

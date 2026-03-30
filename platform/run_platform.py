"""
FX-AlphaLab Platform Launcher
Run this script to start the web dashboard.

Usage:
    python run_platform.py
    Then open http://localhost:8000
"""
import os
import sys
import subprocess
import threading
import webbrowser
from pathlib import Path


def install_deps():
    deps = {"fastapi": "fastapi", "uvicorn": "uvicorn[standard]"}
    for module, package in deps.items():
        try:
            __import__(module)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-q", package],
                stdout=subprocess.DEVNULL,
            )


def main():
    os.chdir(Path(__file__).parent)
    install_deps()

    import uvicorn

    print()
    print("=" * 50)
    print("  FX-AlphaLab Platform")
    print("  Dashboard: http://localhost:8000")
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    print()

    threading.Timer(2.0, lambda: webbrowser.open("http://localhost:8000")).start()
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()

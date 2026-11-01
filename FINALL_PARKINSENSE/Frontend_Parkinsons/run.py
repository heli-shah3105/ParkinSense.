"""
run.py — ParkinSense 2.0 Unified Launcher
=========================================
Runs either:
  1) Full-Stack Web Application (FastAPI + HTML5/CSS3/Vanilla JS Care Suite)
  2) Streamlit Academic & Research Platform
  3) Both simultaneously

Usage:
    python run.py             # Launches Full-Stack Web App (Default, port 8000)
    python run.py --streamlit # Launches Streamlit Companion App (port 8501)
    python run.py --all       # Launches both
"""

import sys
import os
import subprocess
import webbrowser
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def run_fastapi(port=8000, open_browser=True):
    print(f"\n=======================================================")
    print(f"  Starting ParkinSense 2.0 Full-Stack Web Platform")
    print(f"  URL: http://localhost:{port}")
    print(f"  Dashboard: http://localhost:{port}/dashboard/index.html")
    print(f"=======================================================\n")
    if open_browser:
        time.sleep(1.2)
        webbrowser.open(f"http://localhost:{port}")
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=False)


def run_streamlit(port=8501):
    print(f"\n=======================================================")
    print(f"  Starting ParkinSense 2.0 Streamlit Academic App")
    print(f"  URL: http://localhost:{port}")
    print(f"=======================================================\n")
    cmd = [sys.executable, "-m", "streamlit", "run", "app_streamlit.py", "--server.port", str(port)]
    subprocess.run(cmd, cwd=str(BASE_DIR))


def main():
    if "--streamlit" in sys.argv:
        run_streamlit()
    elif "--all" in sys.argv:
        import threading
        t = threading.Thread(target=run_streamlit, daemon=True)
        t.start()
        run_fastapi(port=8000, open_browser=True)
    else:
        run_fastapi(port=8000, open_browser=True)


if __name__ == "__main__":
    main()

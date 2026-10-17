"""
All-in-one runner script for AUTOSAR HLD Document Analysis Assistant.
Usage:
    python run.py --all       # Runs both Backend (FastAPI) and Frontend (Streamlit)
    python run.py --backend   # Runs only FastAPI Backend (Port 8000)
    python run.py --frontend  # Runs only Streamlit Frontend (Port 8501)
"""

import sys
import subprocess
import time
import argparse


def start_backend():
    print("🚀 Starting FastAPI Backend on http://127.0.0.1:8000 ...")
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    )


def start_frontend():
    print("🎨 Starting Streamlit Frontend on http://localhost:8501 ...")
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.headless", "true"]
    )


def main():
    parser = argparse.ArgumentParser(description="AUTOSAR HLD Document Analysis Assistant Launcher")
    parser.add_argument("--backend", action="store_true", help="Launch FastAPI Backend only")
    parser.add_argument("--frontend", action="store_true", help="Launch Streamlit Frontend only")
    parser.add_argument("--all", action="store_true", default=True, help="Launch both Backend and Frontend (default)")
    args = parser.parse_args()

    processes = []

    try:
        if args.backend:
            p_back = start_backend()
            processes.append(p_back)
            p_back.wait()
        elif args.frontend:
            p_front = start_frontend()
            processes.append(p_front)
            p_front.wait()
        else:
            p_back = start_backend()
            processes.append(p_back)
            print("⏳ Waiting for backend to initialize...")
            time.sleep(3)
            p_front = start_frontend()
            processes.append(p_front)

            print("\n" + "=" * 60)
            print("✅ AUTOSAR HLD Analysis Assistant is running!")
            print("👉 Backend API & Docs: http://127.0.0.1:8000/docs")
            print("👉 Streamlit UI:        http://localhost:8501")
            print("👉 Press Ctrl+C to stop all services.")
            print("=" * 60 + "\n")

            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        for p in processes:
            p.terminate()
        print("Done. Goodbye!")


if __name__ == "__main__":
    main()

"""Arranca el backend (FastAPI) y el frontend (Streamlit) con un solo comando: `python run.py`."""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
API_PORT = os.environ.get("API_PORT", "8000")
FRONT_PORT = os.environ.get("FRONTEND_PORT", "8501")


def esperar_backend(url: str, segundos: int = 20) -> bool:
    fin = time.time() + segundos
    while time.time() < fin:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def main() -> int:
    env = {**os.environ, "API_URL": os.environ.get("API_URL", f"http://localhost:{API_PORT}"),
           "FRONTEND_ORIGIN": f"http://localhost:{FRONT_PORT}"}
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", API_PORT, "--log-level", "warning"], cwd=ROOT, env=env)
    if not esperar_backend(f"http://localhost:{API_PORT}/api/health"):
        print("\n[ERROR] El backend no arrancó. Revisa que el puerto", API_PORT, "esté libre y que exista data/evaluaciones.db.")
        backend.terminate()
        return 1
    print(f"\n  Backend listo:  http://localhost:{API_PORT}/docs")
    print(f"  Aplicación:     http://localhost:{FRONT_PORT}\n  (Ctrl+C para detener)\n")
    frontend = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py", "--server.port", FRONT_PORT], cwd=ROOT, env=env)
    try:
        while backend.poll() is None and frontend.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for p in (frontend, backend):
            if p.poll() is None:
                p.terminate()
        for p in (frontend, backend):
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())

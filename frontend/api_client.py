"""Único punto de acceso del frontend a la API.

Nunca lanza excepciones hacia las páginas: siempre devuelve un `Resultado`.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import streamlit as st

# Modo "http": el backend corre aparte (python run.py lo arranca y define API_URL).
# Modo "embebido": si no hay API_URL (p. ej. en Streamlit Community Cloud), la misma API
# FastAPI se ejecuta dentro de este proceso. Los endpoints, validaciones y errores son los mismos.
API_URL = os.environ.get("API_URL", "").rstrip("/")
MODO_EMBEBIDO = not API_URL
TIMEOUT_SEGUNDOS = 10
CACHE_TTL_SEGUNDOS = 60


@st.cache_resource
def _cliente_embebido():
    raiz = str(Path(__file__).resolve().parent.parent)
    if raiz not in sys.path:
        sys.path.insert(0, raiz)
    from fastapi.testclient import TestClient

    from backend.main import app

    return TestClient(app, raise_server_exceptions=False)


@dataclass
class Resultado:
    ok: bool
    data: Any = None
    status: int | None = None
    code: str | None = None
    message: str | None = None


class _ErrorHttp(Exception):
    def __init__(self, status: int, body: Any):
        self.status, self.body = status, body


def _http_get(path: str, params: dict) -> tuple[int, Any]:
    """Petición a la API (HTTP o embebida). En los tests se sustituye por un doble."""
    if MODO_EMBEBIDO:
        r = _cliente_embebido().get(path, params=params)
    else:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=TIMEOUT_SEGUNDOS)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


@st.cache_data(ttl=CACHE_TTL_SEGUNDOS, show_spinner=False)
def _get_cacheado(path: str, params: tuple) -> Any:
    # Solo se cachean respuestas correctas: las excepciones no se guardan en caché.
    status, body = _http_get(path, dict(params))
    if status != 200:
        raise _ErrorHttp(status, body)
    return body


def _get(path: str, **params) -> Resultado:
    params = {k: v for k, v in params.items() if v is not None}
    try:
        return Resultado(ok=True, data=_get_cacheado(path, tuple(sorted(params.items()))), status=200)
    except _ErrorHttp as e:
        err = (e.body or {}).get("error", {}) if isinstance(e.body, dict) else {}
        return Resultado(ok=False, status=e.status, code=err.get("code", "HTTP_ERROR"),
                         message=err.get("message") or f"El servidor respondió con un error ({e.status}).")
    except requests.Timeout:
        return Resultado(ok=False, code="TIMEOUT", message="El servidor tardó demasiado en responder.")
    except requests.ConnectionError:
        return Resultado(ok=False, code="CONNECTION_ERROR", message="No se pudo conectar con el servidor.")
    except Exception:  # noqa: BLE001 - nunca mostrar trazas al usuario
        return Resultado(ok=False, code="UNEXPECTED", message="Se produjo un error inesperado al consultar el servidor.")


def limpiar_cache() -> None:
    _get_cacheado.clear()


# ------------------------------------------------------------------ endpoints
def listar_empleados() -> Resultado:
    return _get("/api/empleados")


def performance(ci: int, desde: str, hasta: str) -> Resultado:
    return _get(f"/api/empleados/{ci}/performance", desde=desde, hasta=hasta)


def comparacion(cis: list[int], desde: str, hasta: str) -> Resultado:
    return _get("/api/comparacion", cis=",".join(str(c) for c in cis), desde=desde, hasta=hasta)


def ranking(turno: str, orden: str, desde: str, hasta: str) -> Resultado:
    return _get("/api/ranking", turno=turno, orden=orden, desde=desde, hasta=hasta)

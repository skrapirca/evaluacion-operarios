"""Errores de la API con formato uniforme: {"error": {"code", "message", "details"}}."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("api")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict | None = None):
        self.status, self.code, self.message, self.details = status, code, message, details or {}


def _respuesta(status: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "details": details or {}}})


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError):
        logger.warning("%s %s params=%s -> %s %s", request.method, request.url.path, dict(request.query_params), exc.status, exc.code)
        return _respuesta(exc.status, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validacion(request: Request, exc: RequestValidationError):
        campos = [".".join(str(p) for p in e.get("loc", [])[1:]) for e in exc.errors()]
        logger.warning("%s %s params=%s -> 400 INVALID_PARAMETER %s", request.method, request.url.path, dict(request.query_params), campos)
        return _respuesta(400, "INVALID_PARAMETER", "Parámetros no válidos.", {"campos": campos})

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return _respuesta(404, "NOT_FOUND", "Recurso no encontrado.")
        return _respuesta(exc.status_code, "HTTP_ERROR", str(exc.detail))

    @app.exception_handler(Exception)
    async def _inesperado(request: Request, exc: Exception):
        logger.exception("%s %s params=%s -> 500", request.method, request.url.path, dict(request.query_params))
        return _respuesta(500, "INTERNAL_ERROR", "Error interno del servidor.")

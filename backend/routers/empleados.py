import sqlite3

from fastapi import APIRouter, Depends, Query

from backend.db import get_db
from backend.errors import ApiError
from backend.routers import validacion
from backend.services import consultas

router = APIRouter(prefix="/api/empleados", tags=["Empleados"])


@router.get("", summary="Lista o busca empleados por nombre o CI (desde el primer carácter)")
def buscar(q: str | None = Query(None, description="Texto a buscar en nombre o CI"), con: sqlite3.Connection = Depends(get_db)):
    if q is None:
        return consultas.listar_empleados(con)
    if not q.strip():
        raise ApiError(400, "INVALID_PARAMETER", "El texto de búsqueda no puede estar vacío.", {"q": q})
    return consultas.buscar_empleados(con, q)


@router.get("/{ci}", summary="Datos básicos de un empleado")
def detalle(ci: int, con: sqlite3.Connection = Depends(get_db)):
    return consultas.obtener_empleado(con, ci)


@router.get("/{ci}/performance", summary="Ficha completa del empleado en un periodo")
def performance(ci: int, desde: str | None = None, hasta: str | None = None, con: sqlite3.Connection = Depends(get_db)):
    d, h = validacion.periodo(desde, hasta)
    return consultas.performance(con, ci, d, h)

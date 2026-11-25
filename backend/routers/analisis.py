import sqlite3

from fastapi import APIRouter, Depends, Query

from backend.db import get_db
from backend.routers import validacion
from backend.services import consultas

router = APIRouter(prefix="/api", tags=["Comparación y ranking"])


@router.get("/comparacion", summary="Compara de 2 a 5 empleados")
def comparacion(cis: str = Query(..., description="CI separados por comas"), desde: str | None = None, hasta: str | None = None,
                con: sqlite3.Connection = Depends(get_db)):
    d, h = validacion.periodo(desde, hasta)
    return consultas.comparacion(con, validacion.lista_cis(cis), d, h)


@router.get("/ranking", summary="Ranking de empleados con filtro por turno")
def ranking(turno: str = "todos", orden: str = "ranking_desc", desde: str | None = None, hasta: str | None = None,
            con: sqlite3.Connection = Depends(get_db)):
    d, h = validacion.periodo(desde, hasta)
    return consultas.ranking(con, validacion.turno(turno), validacion.orden(orden), d, h)

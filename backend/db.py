"""Acceso a la BBDD SQLite (solo lectura)."""
import sqlite3
from typing import Iterator

from backend import config


def conectar() -> sqlite3.Connection:
    ruta = config.db_path()
    if not ruta.exists():
        raise sqlite3.OperationalError(f"No se encuentra la base de datos en {ruta}")
    con = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def get_db() -> Iterator[sqlite3.Connection]:
    """Dependencia de FastAPI: una conexión por petición."""
    con = conectar()
    try:
        yield con
    finally:
        con.close()

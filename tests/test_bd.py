"""5.2 Integridad de la base de datos de demo (data/evaluaciones.db)."""
import sqlite3

import pytest

from conftest import ROOT

BD = ROOT / "data" / "evaluaciones.db"


@pytest.fixture
def con():
    c = sqlite3.connect(BD)
    c.execute("PRAGMA foreign_keys = ON")
    yield c
    c.close()


def test_d01_tres_evaluadores(con):
    evaluadores = {r[0] for r in con.execute("SELECT DISTINCT evaluador FROM evaluaciones")}
    assert evaluadores == {"Gerard", "Irene", "Juan Carlos"}


@pytest.mark.parametrize("tabla", ["evaluaciones", "radar", "ausencias"])
def test_d02_ci_existen_en_empleados(con, tabla):
    huerfanos = con.execute(f"SELECT COUNT(*) FROM {tabla} WHERE ci NOT IN (SELECT ci FROM empleados)").fetchone()[0]
    assert huerfanos == 0


def test_d03_puntajes_en_rango(con):
    assert con.execute("SELECT COUNT(*) FROM evaluaciones WHERE puntaje NOT BETWEEN 1 AND 5").fetchone()[0] == 0


def test_d04_horas_a_dias(con):
    filas = con.execute("SELECT unidades, dias FROM ausencias WHERE unidad_tiempo = 'Hora'").fetchall()
    assert filas
    assert all(abs(d - u / 8) < 1e-3 for u, d in filas)


def test_d05_dias_sin_transformar(con):
    filas = con.execute("SELECT unidades, dias FROM ausencias WHERE unidad_tiempo = 'Día'").fetchall()
    assert filas
    assert all(u == d for u, d in filas)


def test_d06_gravedades_validas(con):
    gravedades = {r[0] for r in con.execute("SELECT DISTINCT gravedad FROM radar")}
    assert gravedades <= {"Leve", "Moderado", "Grave"}


def test_d07_bd_rechaza_puntaje_invalido(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO evaluaciones (ci, fecha, evaluador, aptitud, puntaje, observacion) "
                    "VALUES (575823, '2026-01-01', 'Test', 1, 7, 'x')")
    con.rollback()


def test_d07b_bd_rechaza_ci_inexistente(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO radar (ci, fecha, tipo_incidencia, gravedad, descripcion) VALUES (1, '2026-01-01', 'X', 'Leve', 'x')")
    con.rollback()


def test_d08_filas_coinciden_con_excel(con):
    # Excel: 4 empleados, 12 evaluaciones × 5 aptitudes, 112 conflictos, 56 ausencias (3 vacías, ver incidencias-datos.md).
    cuenta = lambda t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]  # noqa: E731
    assert (cuenta("empleados"), cuenta("evaluaciones"), cuenta("radar"), cuenta("ausencias")) == (4, 60, 112, 53)

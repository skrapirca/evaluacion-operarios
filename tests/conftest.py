"""Fixtures comunes: BBDD de test con datos fijos, independiente de la de demo."""
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "frontend"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

# ------------------------------------------------------------------ datos fijos
EMPLEADOS = [
    (1001, "Ana Lopez", "LOPEZ, ANA", "Mañana", "F"),          # todo 5, sin conflictos ni faltas → 10,0
    (1002, "Bruno Diaz", "DIAZ, BRUNO", "Tarde", "M"),          # caso intermedio
    (1003, "Irene Martin", "MARTIN, IRENE", "Noche", "F"),      # todo 1, 20 graves, 10 días de falta → 1,0
    (1004, "Carlos Peña", "PEÑA, CARLOS", "Noche", "M"),        # sin evaluaciones → "Sin datos"
    (1005, "José Ruiz", "RUIZ, JOSE", "Tarde", "M"),
]
F_EVAL = "2026-03-15"


def _evaluaciones():
    filas = []
    for apt in range(1, 6):
        filas.append((1001, F_EVAL, "Gerard", apt, 5, "Excelente trabajo"))
        filas.append((1003, F_EVAL, "Gerard", apt, 1, "Muy deficiente"))
        filas.append((1005, F_EVAL, "Irene", apt, 3, "Adecuado"))
    for apt, (g, i) in enumerate([(3, 4), (4, 4), (5, 3), (3, 3), (4, 5)], start=1):
        filas.append((1002, F_EVAL, "Gerard", apt, g, f"Observación G{apt}"))
        filas.append((1002, F_EVAL, "Irene", apt, i, f"Observación I{apt}"))
    return filas


RADAR = [
    (1002, "2026-04-01", "Actitud", "Leve", "Llegó tarde", "Expediciones", "Ha rectificado su conducta"),
    (1002, "2026-04-02", "Operacional", "Moderado", "Error de carga", "Expediciones", "No ha rectificado su conducta"),
] + [(1003, "2026-04-03", "Operacional", "Grave", f"Incidente grave {i}", "Producción PAQ", None) for i in range(20)]

AUSENCIAS = [
    (1002, "2026-04-10", "FALTA SIN JUSTIFICAR", 4, "Hora", 0.5),
    (1002, "2026-04-11", "ENFERMEDAD CON BAJA", 2, "Día", 2.0),
    (1002, "2026-04-12", "EXCESO JORNADA, COMPENSACIÓN FESTIVOS, ACUM., ETC", 1, "Día", 1.0),
    (1003, "2026-05-01", "FALTA SIN JUSTIFICAR", 10, "Día", 10.0),
]


def crear_bd(ruta: Path) -> None:
    con = sqlite3.connect(ruta)
    con.executescript((ROOT / "data" / "schema.sql").read_text(encoding="utf-8"))
    con.executemany("INSERT INTO empleados VALUES (?,?,?,?,?)", EMPLEADOS)
    con.executemany("INSERT INTO evaluaciones (ci, fecha, evaluador, aptitud, puntaje, observacion) VALUES (?,?,?,?,?,?)", _evaluaciones())
    con.executemany("INSERT INTO radar (ci, fecha, tipo_incidencia, gravedad, descripcion, area, reaccion_trabajador) VALUES (?,?,?,?,?,?,?)", RADAR)
    con.executemany("INSERT INTO ausencias (ci, fecha, motivo, unidades, unidad_tiempo, dias) VALUES (?,?,?,?,?,?)", AUSENCIAS)
    con.commit()
    con.close()


@pytest.fixture(scope="session")
def ruta_bd_test(tmp_path_factory) -> Path:
    ruta = tmp_path_factory.mktemp("bd") / "test.db"
    crear_bd(ruta)
    return ruta


@pytest.fixture
def client(ruta_bd_test, monkeypatch) -> TestClient:
    monkeypatch.setenv("DB_PATH", str(ruta_bd_test))
    return TestClient(app, raise_server_exceptions=False)

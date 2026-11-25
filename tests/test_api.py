"""5.3 Tests de integración de la API (FastAPI TestClient + BBDD de test)."""
import sqlite3

from backend.db import get_db
from backend.main import app

P = {"desde": "2026-01-01", "hasta": "2026-12-31"}


def _error(r):
    return r.json()["error"]["code"]


def test_a01_busqueda_una_letra(client):
    r = client.get("/api/empleados", params={"q": "i"})
    assert r.status_code == 200
    nombres = {e["nombre"] for e in r.json()}
    assert nombres == {"Irene Martin", "Bruno Diaz", "José Ruiz"}
    assert len(r.json()) <= 10


def test_a01b_busqueda_por_ci(client):
    assert [e["ci"] for e in client.get("/api/empleados", params={"q": "1003"}).json()] == [1003]


def test_a02_sin_q_lista_completa(client):
    r = client.get("/api/empleados")
    assert r.status_code == 200 and len(r.json()) == 5


def test_a03_insensible_a_mayusculas_y_tildes(client):
    a = client.get("/api/empleados", params={"q": "IRÉ"}).json()
    b = client.get("/api/empleados", params={"q": "ire"}).json()
    assert a == b and [e["ci"] for e in a] == [1003]


def test_a04_empleado_inexistente(client):
    r = client.get("/api/empleados/99999")
    assert r.status_code == 404 and _error(r) == "EMPLOYEE_NOT_FOUND"


def test_a05_desde_posterior_a_hasta(client):
    r = client.get("/api/empleados/1002/performance", params={"desde": "2026-12-01", "hasta": "2026-01-01"})
    assert r.status_code == 400 and _error(r) == "INVALID_DATE_RANGE"


def test_a06_fecha_invalida(client):
    r = client.get("/api/empleados/1002/performance", params={"desde": "2026-13-01", "hasta": "2026-12-31"})
    assert r.status_code == 400 and _error(r) == "INVALID_DATE_RANGE"


def test_a07_periodo_sin_datos(client):
    r = client.get("/api/empleados/1002/performance", params={"desde": "2020-01-01", "hasta": "2020-12-31"})
    assert r.status_code == 200
    d = r.json()
    assert d["evaluaciones"]["detalle"] == [] and d["evaluaciones"]["promedio_general"] is None
    assert d["radar"]["detalle"] == [] and d["ausencias"]["detalle"] == []
    assert d["ranking"]["valor"] is None


def test_a08_performance_valida(client):
    d = client.get("/api/empleados/1002/performance", params=P).json()
    proms = {a["id"]: a["promedio"] for a in d["evaluaciones"]["aptitudes"]}
    assert proms == {1: 3.5, 2: 4.0, 3: 4.0, 4: 3.0, 5: 4.5}
    assert d["evaluaciones"]["promedio_general"] == 3.8
    assert d["radar"]["por_gravedad"] == {"Leve": 1, "Moderado": 1, "Grave": 0}
    au = d["ausencias"]
    # La compensación por exceso de jornada (1 día) no computa: 0,5 + 2 = 2,5 días → 1,11 %
    assert au["dias_computables"] == 2.5 and au["porcentaje_ausentismo"] == 1.11
    assert au["dias_falta_sin_justificar"] == 0.5


def test_a09_comparacion_un_ci(client):
    r = client.get("/api/comparacion", params={"cis": "1001", **P})
    assert r.status_code == 400 and _error(r) == "INVALID_COMPARISON_SIZE"


def test_a10_comparacion_seis_ci(client):
    r = client.get("/api/comparacion", params={"cis": "1001,1002,1003,1004,1005,1006", **P})
    assert r.status_code == 400 and _error(r) == "INVALID_COMPARISON_SIZE"


def test_a11_comparacion_duplicados(client):
    r = client.get("/api/comparacion", params={"cis": "1001,1001", **P})
    assert r.status_code == 400 and _error(r) == "INVALID_COMPARISON_SIZE"


def test_a12_comparacion_ci_inexistente(client):
    r = client.get("/api/comparacion", params={"cis": "1001,99999", **P})
    assert r.status_code == 404 and _error(r) == "EMPLOYEE_NOT_FOUND"
    assert r.json()["error"]["details"]["cis"] == [99999]


def test_comparacion_colores(client):
    d = client.get("/api/comparacion", params={"cis": "1001,1002,1003", **P}).json()
    assert d["colores"]["aptitudes"]["1"] == {"1001": "verde", "1002": None, "1003": "rojo"}
    assert d["colores"]["radar"] == {"1001": "verde", "1002": None, "1003": "rojo"}


def test_a13_ranking_por_defecto(client):
    res = client.get("/api/ranking", params=P).json()["resultados"]
    assert [r["empleado"]["ci"] for r in res][0] == 1001
    assert res[0]["ranking"] == 10.0
    assert res[-1]["empleado"]["ci"] == 1004 and res[-1]["ranking"] is None  # "Sin datos" al final
    valores = [r["ranking"] for r in res if r["ranking"] is not None]
    assert valores == sorted(valores, reverse=True)


def test_a14_ranking_turno_noche(client):
    res = client.get("/api/ranking", params={"turno": "Noche", **P}).json()["resultados"]
    assert {r["empleado"]["turno"] for r in res} == {"Noche"} and len(res) == 2


def test_a15_turno_invalido(client):
    r = client.get("/api/ranking", params={"turno": "Madrugada"})
    assert r.status_code == 400 and _error(r) == "INVALID_PARAMETER"


def test_a16_orden_turno_ascendente(client):
    res = client.get("/api/ranking", params={"orden": "turno_asc", **P}).json()["resultados"]
    assert [r["empleado"]["turno"] for r in res] == ["Mañana", "Tarde", "Tarde", "Noche", "Noche"]
    desc = client.get("/api/ranking", params={"orden": "turno_desc", **P}).json()["resultados"]
    assert desc[0]["empleado"]["turno"] == "Noche"


def test_orden_invalido(client):
    r = client.get("/api/ranking", params={"orden": "alfabetico"})
    assert r.status_code == 400 and _error(r) == "INVALID_PARAMETER"


def test_a17_error_de_bd(client):
    def bd_rota():
        raise sqlite3.OperationalError("database is locked")
        yield  # pragma: no cover

    app.dependency_overrides[get_db] = bd_rota
    try:
        r = client.get("/api/empleados")
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 500 and _error(r) == "INTERNAL_ERROR"
    assert "Traceback" not in r.text and "locked" not in r.text


def test_a18_inyeccion_sql(client):
    r = client.get("/api/empleados", params={"q": "' OR 1=1 --"})
    assert r.status_code == 200 and r.json() == []


def test_a19_q_solo_espacios(client):
    r = client.get("/api/empleados", params={"q": "  "})
    assert r.status_code == 400 and _error(r) == "INVALID_PARAMETER"


def test_ruta_inexistente(client):
    r = client.get("/api/no-existe")
    assert r.status_code == 404 and _error(r) == "NOT_FOUND"


def test_parametro_con_tipo_incorrecto(client):
    r = client.get("/api/empleados/abc")
    assert r.status_code == 400 and _error(r) == "INVALID_PARAMETER"


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "empleados": 5}

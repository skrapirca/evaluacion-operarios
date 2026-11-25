"""5.4 y 5.5 Tests de pantallas con Streamlit AppTest.

- 5.4 (F): el cliente de la API se conecta a la API real con la BBDD de test, o se sustituye
  por un doble que simula errores (500, servidor caído).
- 5.5 (E): flujos completos contra la API real con la BBDD de test.
"""
from datetime import date

import pytest
import requests
from streamlit.testing.v1 import AppTest

import api_client
import utils
from conftest import ROOT

APP = str(ROOT / "frontend" / "app.py")
PERIODO = {"desde": "2026-01-01", "hasta": "2026-12-31"}


# ------------------------------------------------------------------ dobles del cliente HTTP
@pytest.fixture
def llamadas():
    return []


@pytest.fixture
def api_real(client, monkeypatch, llamadas):
    """El frontend llama a la API real (TestClient) con la BBDD de test."""
    def _http_get(path, params):
        llamadas.append(path)
        r = client.get(path, params=params)
        return r.status_code, r.json()

    monkeypatch.setattr(api_client, "_http_get", _http_get)
    api_client.limpiar_cache()
    yield
    api_client.limpiar_cache()


@pytest.fixture
def api_500(api_real, client, monkeypatch):
    """Lista de empleados correcta, pero el resto de endpoints devuelve 500."""
    def _http_get(path, params):
        if path == "/api/empleados":
            r = client.get(path, params=params)
            return r.status_code, r.json()
        return 500, {"error": {"code": "INTERNAL_ERROR", "message": "Error interno del servidor."}}

    monkeypatch.setattr(api_client, "_http_get", _http_get)


@pytest.fixture
def api_caida(monkeypatch):
    def _http_get(path, params):
        raise requests.ConnectionError("Connection refused")

    monkeypatch.setattr(api_client, "_http_get", _http_get)
    api_client.limpiar_cache()
    yield
    api_client.limpiar_cache()


def abrir(pagina: str, **query) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=30)
    at.switch_page(f"views/{pagina}.py")
    for k, v in query.items():
        at.query_params[k] = v
    return at.run()


def htmls(at: AppTest) -> str:
    return "\n".join(h.proto.body for h in at.get("html"))


def textos(elementos) -> str:
    return "\n".join(e.value for e in elementos)


def sin_excepciones(at: AppTest) -> None:
    assert len(at.exception) == 0, [e.value for e in at.exception]


# ------------------------------------------------------------------ 5.4 Frontend
def test_f01_f02_buscador_por_nombre_y_ci(api_real):
    at = abrir("performance")
    sb = at.selectbox(key="perf_empleado")
    # El filtro integrado de Streamlit ("contains") busca en estas etiquetas desde la 1.ª letra.
    assert "Irene Martin (1003)" in sb.options and "Bruno Diaz (1002)" in sb.options
    assert sb.value is None
    assert "Busca un empleado" in textos(at.info)


def test_f03_periodo_incompleto(api_real, llamadas):
    at = abrir("performance", ci="1002", **PERIODO)
    llamadas.clear()
    at.date_input(key="perf_periodo").set_value((date(2026, 1, 1),)).run()
    assert "Selecciona un periodo completo" in textos(at.warning)
    assert not any("/performance" in p for p in llamadas)


def test_f04_tooltip_ausentismo(api_real):
    at = abrir("performance", ci="1002", **PERIODO)
    ayudas = {m.label: m.proto.help for m in at.metric}
    assert "225 días" in ayudas["Ausentismo"] and "225 días" in ayudas["% de ausentismo"]


def test_f05_tooltip_ranking(api_real):
    at = abrir("ranking")
    assert "promedio de aptitudes (70%)" in htmls(at)
    assert "title=" in htmls(at)


def test_f06_comparacion_un_empleado(api_real):
    at = abrir("comparacion")
    at.multiselect(key="comp_empleados").set_value([1001]).run()
    assert "al menos 2 empleados" in textos(at.warning)


def test_f07_error_500(api_500):
    at = abrir("performance", ci="1002", **PERIODO)
    sin_excepciones(at)
    assert "error del servidor" in textos(at.error)
    assert any(b.label == "Reintentar" for b in at.button)
    assert "Traceback" not in htmls(at)


def test_f08_backend_caido(api_caida):
    at = abrir("performance")
    sin_excepciones(at)
    assert "No se pudo conectar con el servidor" in textos(at.error)
    assert any(b.label == "Reintentar" for b in at.button)


def test_f09_empleado_no_encontrado(api_real):
    at = abrir("performance", ci="99999")
    sin_excepciones(at)
    assert "Empleado no encontrado" in textos(at.error)


def test_f10_ficha_desde_url(api_real):
    at = abrir("performance", ci="1002", **PERIODO)
    sin_excepciones(at)
    assert at.selectbox(key="perf_empleado").value == 1002
    assert at.date_input(key="perf_periodo").value == (date(2026, 1, 1), date(2026, 12, 31))
    assert "Bruno Diaz" in htmls(at)


def test_f11_ranking_de_mejor_a_peor(api_real):
    at = abrir("ranking")
    at.date_input(key="rank_periodo").set_value((date(2026, 1, 1), date(2026, 12, 31))).run()
    cuerpo = htmls(at)
    orden = [cuerpo.index(n) for n in ("Ana Lopez", "Bruno Diaz", "José Ruiz", "Irene Martin", "Carlos Peña")]
    assert orden == sorted(orden)
    assert "Sin datos" in cuerpo


def test_f12_colores_comparacion(api_real):
    at = abrir("comparacion")
    at.date_input(key="comp_periodo").set_value((date(2026, 1, 1), date(2026, 12, 31)))
    at.multiselect(key="comp_empleados").set_value([1001, 1002, 1003]).run()
    tablas = [h.proto.body for h in at.get("html") if h.proto.body.startswith("<table")]
    aptitudes, radar, ausencias = tablas
    assert "data-color='verde'" in aptitudes and "data-color='rojo'" in aptitudes
    assert "data-color='verde'" in radar and "data-color='rojo'" in radar
    assert "data-color" not in ausencias


# ------------------------------------------------------------------ 5.5 Flujos completos
def test_e01_flujo_performance(api_real):
    at = abrir("performance")
    at.date_input(key="perf_periodo").set_value((date(2026, 1, 1), date(2026, 12, 31)))
    at.selectbox(key="perf_empleado").set_value(1002).run()
    sin_excepciones(at)
    cabeceras = [h.value for h in at.header]
    assert cabeceras == ["Aptitudes", "Conflictos · Radar", "Ausencias", "Detalle"]
    assert len(at.dataframe) == 3  # detalle de evaluaciones, conflictos y ausencias
    assert at.query_params["ci"] == "1002"


def test_e02_flujo_comparacion_ver_ficha(api_real):
    at = abrir("comparacion")
    at.date_input(key="comp_periodo").set_value((date(2026, 1, 1), date(2026, 12, 31)))
    at.multiselect(key="comp_empleados").set_value([1001, 1002, 1005]).run()
    sin_excepciones(at)
    enlaces = [p.proto for p in at.get("page_link") if p.proto.label.startswith("Ver ficha")]
    assert len(enlaces) == 3
    assert all("desde=2026-01-01" in e.query_string and "hasta=2026-12-31" in e.query_string for e in enlaces)
    assert "ci=1002" in enlaces[1].query_string


def test_e03_flujo_ranking_filtrar_y_ordenar(api_real):
    at = abrir("ranking")
    at.date_input(key="rank_periodo").set_value((date(2026, 1, 1), date(2026, 12, 31)))
    at.selectbox(key="rank_turno").set_value("Noche").run()
    cuerpo = htmls(at)
    assert "Irene Martin" in cuerpo and "Carlos Peña" in cuerpo and "Ana Lopez" not in cuerpo
    at.selectbox(key="rank_orden").set_value("Ranking: de peor a mejor").run()
    cuerpo = htmls(at)
    # Peor primero; "Sin datos" siempre al final.
    assert cuerpo.index("Irene Martin") < cuerpo.index("Carlos Peña")
    sin_excepciones(at)


def test_inicio(api_real):
    at = abrir("inicio")
    sin_excepciones(at)
    assert {"Entrar →"} == {p.proto.label for p in at.get("page_link")}

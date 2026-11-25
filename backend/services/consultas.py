"""Consultas a la BBDD y composición de las respuestas de la API."""
from __future__ import annotations

import sqlite3
from datetime import date

from backend import config
from backend.errors import ApiError
from backend.services import calculos as calc


# ---------------------------------------------------------------- utilidades
def _filtro_periodo(columna: str, desde: date | None, hasta: date | None) -> tuple[str, list]:
    sql, params = "", []
    if desde:
        sql += f" AND date({columna}) >= ?"
        params.append(desde.isoformat())
    if hasta:
        sql += f" AND date({columna}) <= ?"
        params.append(hasta.isoformat())
    return sql, params


def _empleado_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in ("ci", "nombre", "nombre_original", "turno", "genero")}


# ---------------------------------------------------------------- empleados
def listar_empleados(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute("SELECT * FROM empleados ORDER BY nombre").fetchall()
    return [_empleado_dict(r) for r in rows]


def buscar_empleados(con: sqlite3.Connection, q: str) -> list[dict]:
    termino = calc.normalizar_texto(q)
    res = [
        e for e in listar_empleados(con)
        if termino in calc.normalizar_texto(e["nombre"])
        or termino in calc.normalizar_texto(e["nombre_original"])
        or termino in str(e["ci"])
    ]
    return res[: config.MAX_RESULTADOS_BUSQUEDA]


def obtener_empleado(con: sqlite3.Connection, ci: int) -> dict:
    row = con.execute("SELECT * FROM empleados WHERE ci = ?", (ci,)).fetchone()
    if row is None:
        raise ApiError(404, "EMPLOYEE_NOT_FOUND", f"No existe ningún empleado con CI {ci}.", {"ci": ci})
    return _empleado_dict(row)


# ---------------------------------------------------------------- datos por empleado
def _evaluaciones(con, ci, desde, hasta) -> list[dict]:
    f, p = _filtro_periodo("fecha", desde, hasta)
    rows = con.execute(
        f"SELECT fecha, evaluador, aptitud, puntaje, observacion FROM evaluaciones WHERE ci = ?{f} ORDER BY fecha, evaluador, aptitud",
        [ci, *p],
    ).fetchall()
    return [dict(r) for r in rows]


def _radar(con, ci, desde, hasta) -> list[dict]:
    f, p = _filtro_periodo("fecha", desde, hasta)
    rows = con.execute(
        f"""SELECT fecha, tipo_incidencia, gravedad, descripcion, area, titulo, accion_realizada,
                   reaccion_trabajador, observaciones
            FROM radar WHERE ci = ?{f} ORDER BY fecha DESC""",
        [ci, *p],
    ).fetchall()
    return [dict(r) for r in rows]


def _ausencias(con, ci, desde, hasta) -> list[dict]:
    f, p = _filtro_periodo("fecha", desde, hasta)
    rows = con.execute(
        f"""SELECT fecha, fecha_fin, motivo, hora_inicio, hora_fin, unidades, unidad_tiempo, dias
            FROM ausencias WHERE ci = ?{f} ORDER BY fecha DESC""",
        [ci, *p],
    ).fetchall()
    return [dict(r) for r in rows]


def _indicadores(evals: list[dict], conflictos: list[dict], ausencias: list[dict]) -> dict:
    prom_apt = calc.promedios_por_aptitud(evals)
    prom_gen = calc.promedio_general(prom_apt)
    conteo = calc.contar_gravedades(c["gravedad"] for c in conflictos)
    dias_falta = round(sum(a["dias"] for a in ausencias if calc.es_falta_sin_justificar(a["motivo"])), 4)
    ranking = calc.calcular_ranking(prom_gen, conteo, dias_falta)
    componentes = None
    if prom_gen is not None:
        componentes = {
            "aptitudes": round(calc.componente_aptitudes(prom_gen), 3),
            "conflictos": round(calc.componente_conflictos(conteo), 3),
            "ausencias": round(calc.componente_ausencias(dias_falta), 3),
        }
    return {
        "prom_apt": prom_apt, "prom_gen": prom_gen, "conteo": conteo, "dias_falta": dias_falta,
        "ranking": {"valor": ranking, "componentes": componentes, "penalizacion_conflictos": calc.penalizacion_conflictos(conteo),
                    "dias_falta_sin_justificar": dias_falta},
    }


def _ausencias_por_motivo(ausencias: list[dict]) -> list[dict]:
    por: dict[str, dict] = {}
    for a in ausencias:
        m = por.setdefault(a["motivo"], {"motivo": a["motivo"], "cantidad": 0, "dias": 0.0, "computa": calc.computa_ausentismo(a["motivo"])})
        m["cantidad"] += 1
        m["dias"] = round(m["dias"] + a["dias"], 2)
    return sorted(por.values(), key=lambda m: -m["dias"])


# ---------------------------------------------------------------- performance
def performance(con, ci: int, desde: date | None, hasta: date | None) -> dict:
    empleado = obtener_empleado(con, ci)
    evals, conflictos, ausencias = _evaluaciones(con, ci, desde, hasta), _radar(con, ci, desde, hasta), _ausencias(con, ci, desde, hasta)
    ind = _indicadores(evals, conflictos, ausencias)

    aptitudes = []
    for apt_id, nombre in config.APTITUDES.items():
        de_apt = [e for e in evals if e["aptitud"] == apt_id]
        aptitudes.append({
            "id": apt_id, "nombre": nombre, "promedio": ind["prom_apt"][apt_id],
            "resumen": calc.resumen_observaciones(de_apt) if de_apt else None,
        })

    por_tipo: dict[str, dict] = {}
    for c in conflictos:
        t = por_tipo.setdefault(c["tipo_incidencia"], {"tipo": c["tipo_incidencia"], **{g: 0 for g in config.GRAVEDADES}, "total": 0})
        t[c["gravedad"]] += 1
        t["total"] += 1

    dias_computables = round(sum(a["dias"] for a in ausencias if calc.computa_ausentismo(a["motivo"])), 2)
    for e in evals:
        e["aptitud_nombre"] = config.APTITUDES[e["aptitud"]]
        e["puntaje_texto"] = config.ESCALA[e["puntaje"]]
    for a in ausencias:
        a["computa"] = calc.computa_ausentismo(a["motivo"])

    return {
        "empleado": empleado,
        "periodo": {"desde": desde.isoformat() if desde else None, "hasta": hasta.isoformat() if hasta else None},
        "evaluaciones": {
            "cantidad": len({(e["fecha"], e["evaluador"]) for e in evals}),
            "evaluadores": sorted({e["evaluador"] for e in evals}),
            "promedio_general": ind["prom_gen"],
            "aptitudes": aptitudes,
            "detalle": evals,
        },
        "radar": {
            "total": len(conflictos),
            "por_gravedad": ind["conteo"],
            "por_tipo": sorted(por_tipo.values(), key=lambda t: -t["total"]),
            "resumen": calc.resumen_radar(conflictos),
            "detalle": conflictos,
        },
        "ausencias": {
            "total_registros": len(ausencias),
            "dias_totales": round(sum(a["dias"] for a in ausencias), 2),
            "dias_computables": dias_computables,
            "porcentaje_ausentismo": calc.porcentaje_ausentismo(dias_computables),
            "dias_laborables": config.DIAS_LABORABLES,
            "dias_falta_sin_justificar": ind["dias_falta"],
            "por_motivo": _ausencias_por_motivo(ausencias),
            "detalle": ausencias,
        },
        "ranking": ind["ranking"],
    }


# ---------------------------------------------------------------- comparación
def comparacion(con, cis: list[int], desde, hasta) -> dict:
    inexistentes = [ci for ci in cis if con.execute("SELECT 1 FROM empleados WHERE ci = ?", (ci,)).fetchone() is None]
    if inexistentes:
        raise ApiError(404, "EMPLOYEE_NOT_FOUND", f"No existen empleados con CI: {', '.join(map(str, inexistentes))}.", {"cis": inexistentes})

    filas, motivos = [], set()
    for ci in cis:
        emp = obtener_empleado(con, ci)
        evals, conflictos, ausencias = _evaluaciones(con, ci, desde, hasta), _radar(con, ci, desde, hasta), _ausencias(con, ci, desde, hasta)
        ind = _indicadores(evals, conflictos, ausencias)
        por_motivo = {m["motivo"]: m["dias"] for m in _ausencias_por_motivo(ausencias)}
        motivos.update(por_motivo)
        filas.append({
            "empleado": emp, "ranking": ind["ranking"], "promedio_general": ind["prom_gen"],
            "aptitudes": {str(k): v for k, v in ind["prom_apt"].items()},
            "radar": ind["conteo"], "ausencias_por_motivo": por_motivo,
        })

    colores_apt = {
        str(a): calc.colores_comparacion({str(f["empleado"]["ci"]): f["aptitudes"][str(a)] for f in filas})
        for a in config.APTITUDES
    }
    return {
        "periodo": {"desde": desde.isoformat() if desde else None, "hasta": hasta.isoformat() if hasta else None},
        "aptitudes": {str(k): v for k, v in config.APTITUDES.items()},
        "empleados": filas,
        "motivos_ausencia": sorted(motivos),
        "colores": {
            "aptitudes": colores_apt,
            "promedio_general": calc.colores_comparacion({str(f["empleado"]["ci"]): f["promedio_general"] for f in filas}),
            "radar": calc.colores_radar({str(f["empleado"]["ci"]): f["radar"] for f in filas}),
        },
    }


# ---------------------------------------------------------------- ranking
def ranking(con, turno: str, orden: str, desde, hasta) -> dict:
    empleados = listar_empleados(con)
    if turno != "todos":
        empleados = [e for e in empleados if e["turno"] == turno]
    res = []
    for e in empleados:
        ci = e["ci"]
        ind = _indicadores(_evaluaciones(con, ci, desde, hasta), _radar(con, ci, desde, hasta), _ausencias(con, ci, desde, hasta))
        res.append({"empleado": e, "ranking": ind["ranking"]["valor"], "promedio_general": ind["prom_gen"]})

    # Por ranking: "Sin datos" siempre al final.
    def clave_ranking(r, desc: bool):
        v = r["ranking"]
        return (v is None, -(v or 0) if desc else (v or 0), r["empleado"]["nombre"])

    if orden == "ranking_desc":
        res.sort(key=lambda r: clave_ranking(r, True))
    elif orden == "ranking_asc":
        res.sort(key=lambda r: clave_ranking(r, False))
    else:
        # Por turno (orden lógico Mañana < Tarde < Noche); dentro de cada turno, mejor ranking primero.
        res.sort(key=lambda r: clave_ranking(r, True))
        idx = {t: i for i, t in enumerate(config.TURNOS)}
        res.sort(key=lambda r: idx.get(r["empleado"]["turno"], 99), reverse=(orden == "turno_desc"))

    # Posición según ranking (independiente del orden visual).
    ordenados = sorted([r for r in res if r["ranking"] is not None], key=lambda r: -r["ranking"])
    pos = {r["empleado"]["ci"]: i + 1 for i, r in enumerate(ordenados)}
    for r in res:
        r["posicion"] = pos.get(r["empleado"]["ci"])

    return {
        "periodo": {"desde": desde.isoformat() if desde else None, "hasta": hasta.isoformat() if hasta else None},
        "filtros": {"turno": turno, "orden": orden},
        "resultados": res,
    }

import html

import pandas as pd
import streamlit as st

import api_client as api
import utils
from components import ui

ui.cabecera("Performance de empleado", "Ficha individual del trabajador en el periodo seleccionado")

# --- Parámetros de la URL (?ci=...&desde=...&hasta=...) -------------------------
qp = st.query_params
ci_url = qp.get("ci")
desde_url, hasta_url = utils.parse_fecha(qp.get("desde")), utils.parse_fecha(qp.get("hasta"))

empleados = ui.cargar_empleados()
cis_validos = {e["ci"] for e in empleados}

ci_inicial = None
if ci_url is not None:
    try:
        ci_inicial = int(ci_url)
    except ValueError:
        ci_inicial = None
    if ci_inicial not in cis_validos:
        ui.empleado_no_encontrado(ci_url)
        st.stop()

# --- Filtros -----------------------------------------------------------------------
c1, c2 = st.columns([3, 2], gap="medium")
with c1:
    seleccionado = ui.buscador_empleado(empleados, key="perf_empleado", ci_inicial=ci_inicial)
with c2:
    periodo = ui.filtro_periodo("perf_periodo", desde_url, hasta_url)

if seleccionado is None:
    st.info("Busca un empleado por nombre o CI para ver su ficha.")
    st.stop()
if periodo is None:
    st.stop()

desde, hasta = (d.isoformat() for d in periodo)
st.query_params.update({"ci": str(seleccionado["ci"]), "desde": desde, "hasta": hasta})

with st.spinner("Cargando ficha…"):
    res = api.performance(seleccionado["ci"], desde, hasta)
if not res.ok:
    if res.code == "EMPLOYEE_NOT_FOUND":
        ui.empleado_no_encontrado(seleccionado["ci"])
    else:
        ui.mostrar_error(res)
    st.stop()

d = res.data
ev, rd, au = d["evaluaciones"], d["radar"], d["ausencias"]
st.html("<hr class='eo-linea'>")

# --- Cabecera: ficha + resumen general ------------------------------------------------
col_ficha, col_resumen = st.columns([1, 3], gap="large")
with col_ficha:
    st.html(ui.ficha_empleado_html(d["empleado"]))
    st.html(f"<div style='text-align:center;margin-top:.6rem'>{ui.ranking_html(d['ranking']['valor'])}</div>")

with col_resumen:
    prom = ev["promedio_general"]
    color = utils.color_promedio(prom)
    k1, k2, k3 = st.columns(3)
    with k1:
        estilo = f"color:{utils.COLORES[color]}" if color else ""
        st.html(
            f"<div class='eo-kpi-label'>Promedio general</div>"
            f"<div class='eo-kpi-valor' style='{estilo}' data-color='{color or ''}'>{utils.formato_numero(prom)}</div>"
            f"{ui.estrellas_html(prom)}"
        )
    with k2:
        st.metric("Evaluaciones", ev["cantidad"], help="Evaluadores: " + (", ".join(ev["evaluadores"]) or "—"))
    with k3:
        st.metric("Ausentismo", f"{utils.formato_numero(au['porcentaje_ausentismo'])} %", help=utils.TEXTO_INFO_AUSENTISMO)

    if ev["cantidad"] == 0:
        st.info("No hay evaluaciones en el periodo seleccionado.")

# --- Aptitudes -------------------------------------------------------------------------------
st.header("Aptitudes")
if ev["cantidad"] == 0:
    st.info("No hay evaluaciones en el periodo seleccionado.")
else:
    bloques = []
    for a in ev["aptitudes"]:
        c = utils.color_promedio(a["promedio"])
        ancho = (a["promedio"] or 0) / 5 * 100
        col = utils.COLORES.get(c, "#BFB4A5")
        bloques.append(
            f"<div class='eo-apt'><div class='eo-apt-cab'><span class='eo-apt-nombre'>{a['id']}. {html.escape(a['nombre'])}</span>"
            f"<span class='eo-apt-valor' style='color:{col}'>{utils.formato_numero(a['promedio'])} {ui.estrellas_html(a['promedio'])}</span></div>"
            f"<div class='eo-barra'><div style='width:{ancho:.0f}%;background:{col}'></div></div>"
            f"<div class='eo-apt-resumen'>{html.escape(a['resumen'] or '')}</div></div>"
        )
    st.html("".join(bloques))

# --- Radar ------------------------------------------------------------------------------------
st.header("Conflictos · Radar")
if rd["total"] == 0:
    st.info("Sin conflictos registrados en el periodo.")
else:
    g = rd["por_gravedad"]
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total", rd["total"])
    r2.metric("Leves", g["Leve"])
    r3.metric("Moderados", g["Moderado"])
    r4.metric("Graves", g["Grave"])
    filas = [[t["tipo"], str(t["Leve"]), str(t["Moderado"]), str(t["Grave"]), str(t["total"])] for t in rd["por_tipo"]]
    filas.append(["Total", str(g["Leve"]), str(g["Moderado"]), str(g["Grave"]), str(rd["total"])])
    st.html(ui.tabla_html(["Tipo de incidencia", "Leve", "Moderado", "Grave", "Total"], filas,
                          clases_fila=[None] * (len(filas) - 1) + ["eo-total"]))
    st.caption(rd["resumen"])

# --- Ausencias -------------------------------------------------------------------------------
st.header("Ausencias")
if au["total_registros"] == 0:
    st.info("Sin ausencias registradas en el periodo.")
else:
    a1, a2, a3 = st.columns(3)
    a1.metric("% de ausentismo", f"{utils.formato_numero(au['porcentaje_ausentismo'])} %", help=utils.TEXTO_INFO_AUSENTISMO)
    a2.metric("Días que computan", utils.formato_numero(au["dias_computables"]),
              help=f"Sobre {au['dias_laborables']} días laborables.")
    a3.metric("Días de falta sin justificar", utils.formato_numero(au["dias_falta_sin_justificar"]),
              help="Único motivo que penaliza en el ranking.")
    filas = [[m["motivo"], str(m["cantidad"]), utils.formato_numero(m["dias"]), "Sí" if m["computa"] else "No"] for m in au["por_motivo"]]
    st.html(ui.tabla_html(["Motivo", "Nº", "Días", "Computa en %"], filas))

# --- Detalle ---------------------------------------------------------------------------------
st.header("Detalle")
t1, t2, t3 = st.tabs([f"Evaluaciones ({len(ev['detalle'])})", f"Conflictos ({rd['total']})", f"Ausencias ({au['total_registros']})"])
with t1:
    if ev["detalle"]:
        df = pd.DataFrame(ev["detalle"])[["fecha", "evaluador", "aptitud_nombre", "puntaje", "puntaje_texto", "observacion"]]
        df.columns = ["Fecha", "Evaluador", "Aptitud", "Puntaje", "Valoración", "Observación"]
        st.dataframe(df, hide_index=True, width="stretch")
    else:
        st.info("No hay evaluaciones en el periodo seleccionado.")
with t2:
    if rd["detalle"]:
        df = pd.DataFrame(rd["detalle"])[["fecha", "tipo_incidencia", "gravedad", "area", "descripcion", "accion_realizada",
                                          "reaccion_trabajador", "observaciones"]]
        df.columns = ["Fecha", "Tipo", "Gravedad", "Área", "Descripción", "Acción realizada", "Reacción", "Observaciones"]
        st.dataframe(df, hide_index=True, width="stretch")
    else:
        st.info("Sin conflictos registrados en el periodo.")
with t3:
    if au["detalle"]:
        df = pd.DataFrame(au["detalle"])
        df["computa"] = df["computa"].map({True: "Sí", False: "No"})
        df = df[["fecha", "fecha_fin", "motivo", "unidades", "unidad_tiempo", "hora_inicio", "hora_fin", "dias", "computa"]]
        df.columns = ["Inicio", "Fin", "Motivo", "Unidades", "Unidad", "Hora inicio", "Hora fin", "Días", "Computa en %"]
        st.dataframe(df, hide_index=True, width="stretch")
    else:
        st.info("Sin ausencias registradas en el periodo.")

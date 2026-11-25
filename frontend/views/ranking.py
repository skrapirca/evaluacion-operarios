import streamlit as st

import api_client as api
import utils
from components import ui

ui.cabecera("Ranking de empleados", "Clasificación de 1 a 10 por turno y periodo")

c1, c2, c3 = st.columns([1, 1.4, 2], gap="medium")
with c1:
    turno = st.selectbox("Turno", utils.TURNOS, key="rank_turno")
with c2:
    orden_label = st.selectbox("Ordenar por", list(utils.ORDENES), key="rank_orden")
with c3:
    periodo = ui.filtro_periodo("rank_periodo")

if periodo is None:
    st.stop()

desde, hasta = (d.isoformat() for d in periodo)
with st.spinner("Calculando ranking…"):
    res = api.ranking(turno.lower() if turno == "Todos" else turno, utils.ORDENES[orden_label], desde, hasta)
if not res.ok:
    ui.mostrar_error(res)
    st.stop()

resultados = res.data["resultados"]
if not resultados:
    st.info("No hay empleados para los filtros seleccionados.")
    st.stop()

st.html(f"<div class='eo-sub'>{len(resultados)} empleados · ⓘ {utils.TEXTO_INFO_RANKING}</div>")

POR_FILA = 4
for inicio in range(0, len(resultados), POR_FILA):
    cols = st.columns(POR_FILA, gap="small")
    for col, r in zip(cols, resultados[inicio:inicio + POR_FILA]):
        with col, st.container(border=True):
            pos = f"Nº {r['posicion']}" if r["posicion"] else "Sin datos"
            st.html(f"<div class='eo-posicion' style='text-align:center'>{pos}</div>")
            st.html(ui.ficha_empleado_html(r["empleado"], pequena=True))
            st.html(f"<div style='text-align:center;margin:.4rem 0'>{ui.ranking_html(r['ranking'])}</div>")
            st.page_link("views/performance.py", label="Ver ficha →",
                         query_params={"ci": str(r["empleado"]["ci"]), "desde": desde, "hasta": hasta})

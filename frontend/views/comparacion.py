import streamlit as st

import api_client as api
import utils
from components import ui

ui.cabecera("Comparación de empleados", "Compara de 2 a 5 empleados en el mismo periodo")

empleados = ui.cargar_empleados()
por_ci = {e["ci"]: e for e in empleados}

c1, c2 = st.columns([3, 2], gap="medium")
with c1:
    seleccion = st.multiselect(
        "Empleados (de 2 a 5)", list(por_ci), key="comp_empleados", max_selections=5,
        format_func=lambda c: utils.etiqueta_empleado(por_ci[c]), placeholder="Buscar por nombre o CI…",
    )
with c2:
    periodo = ui.filtro_periodo("comp_periodo")

if len(seleccion) < 2:
    st.warning("Selecciona al menos 2 empleados para comparar (máximo 5).")
    st.stop()
if periodo is None:
    st.stop()

desde, hasta = (d.isoformat() for d in periodo)
with st.spinner("Comparando…"):
    res = api.comparacion(seleccion, desde, hasta)
if not res.ok:
    ui.mostrar_error(res)
    st.stop()

d = res.data
filas_emp = d["empleados"]
nombres = [f["empleado"]["nombre"] for f in filas_emp]
cis = [str(f["empleado"]["ci"]) for f in filas_emp]
st.html("<hr class='eo-linea'>")

# --- Fichas ------------------------------------------------------------------------------------
for col, f in zip(st.columns(len(filas_emp), gap="small"), filas_emp):
    with col, st.container(border=True):
        st.html(ui.ficha_empleado_html(f["empleado"], pequena=True))
        st.html(f"<div style='text-align:center;margin:.4rem 0'>{ui.ranking_html(f['ranking']['valor'])}</div>")
        st.page_link("views/performance.py", label="Ver ficha →",
                     query_params={"ci": str(f["empleado"]["ci"]), "desde": desde, "hasta": hasta})

# --- Aptitudes -----------------------------------------------------------------------------------
st.header("Aptitudes")
if all(f["promedio_general"] is None for f in filas_emp):
    st.info("No hay evaluaciones en el periodo seleccionado.")
else:
    filas, estilos = [], []
    for apt_id, apt_nombre in d["aptitudes"].items():
        colores = d["colores"]["aptitudes"][apt_id]
        filas.append([f"{apt_id}. {apt_nombre}"] + [utils.formato_numero(f["aptitudes"][apt_id]) for f in filas_emp])
        estilos.append([colores.get(ci) for ci in cis])
    filas.append(["Promedio general"] + [utils.formato_numero(f["promedio_general"]) for f in filas_emp])
    estilos.append([d["colores"]["promedio_general"].get(ci) for ci in cis])
    st.html(ui.tabla_html(["Aptitud"] + nombres, filas, estilos, clases_fila=[None] * (len(filas) - 1) + ["eo-total"]))
    st.html("<div class='eo-leyenda'>Verde: puntaje más alto de cada aptitud · Rojo: el más bajo. Los empates se colorean igual.</div>")

# --- Radar -----------------------------------------------------------------------------------------
st.header("Conflictos · Radar")
col_radar = d["colores"]["radar"]
filas = [[g] + [str(f["radar"][g]) for f in filas_emp] for g in ("Leve", "Moderado", "Grave")]
filas.append(["Total"] + [str(sum(f["radar"].values())) for f in filas_emp])
estilos = [[col_radar.get(ci) for ci in cis] for _ in filas]
st.html(ui.tabla_html(["Gravedad"] + nombres, filas, estilos, clases_fila=[None, None, None, "eo-total"]))
st.html("<div class='eo-leyenda'>Verde: mejor resultado (menos conflictos graves; a igualdad, menos moderados y luego menos leves) · Rojo: peor resultado.</div>")

# --- Ausentismo (sin colores) -------------------------------------------------------------------
st.header("Ausencias por motivo (días)")
if not d["motivos_ausencia"]:
    st.info("Sin ausencias registradas en el periodo.")
else:
    filas = [[m] + [utils.formato_numero(f["ausencias_por_motivo"].get(m, 0)) for f in filas_emp] for m in d["motivos_ausencia"]]
    st.html(ui.tabla_html(["Motivo"] + nombres, filas))

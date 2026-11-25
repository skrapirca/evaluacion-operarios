import streamlit as st

st.html(
    "<div class='eo-hero'><h1>Evaluación de operarios</h1>"
    "<p>Desempeño, conflictos y ausentismo del personal del centro</p></div>"
)

TARJETAS = [
    ("01", "Performance de empleado", "Ficha individual: aptitudes, conflictos del Radar, ausencias y detalle.",
     "views/performance.py"),
    ("02", "Comparación de empleados", "Compara de 2 a 5 empleados aptitud por aptitud.", "views/comparacion.py"),
    ("03", "Ranking de empleados", "Clasificación de 1 a 10 con filtro por turno y periodo.", "views/ranking.py"),
]

columnas = st.columns(3, gap="medium")
for col, (num, titulo, texto, destino) in zip(columnas, TARJETAS):
    with col, st.container(border=True):
        st.html(
            f"<div class='eo-card-num'>{num}</div><div class='eo-card-titulo'>{titulo}</div>"
            f"<div class='eo-card-texto'>{texto}</div>"
        )
        st.page_link(destino, label="Entrar →")

"""Punto de entrada del frontend: `streamlit run frontend/app.py`."""
import logging

import streamlit as st

from components import ui

st.set_page_config(page_title="Evaluación de operarios", page_icon="◻", layout="wide")
ui.cargar_estilos()

paginas = [
    st.Page("views/inicio.py", title="Inicio", url_path="inicio", default=True),
    st.Page("views/performance.py", title="Performance", url_path="performance"),
    st.Page("views/comparacion.py", title="Comparación", url_path="comparacion"),
    st.Page("views/ranking.py", title="Ranking", url_path="ranking"),
]
pagina = st.navigation(paginas, position="top")

try:
    pagina.run()
except Exception:  # Red de seguridad global: nunca dejar la pantalla en blanco ni mostrar trazas.
    logging.getLogger("frontend").exception("Error no controlado en la página %s", pagina.title)
    st.error("Se produjo un error inesperado al mostrar esta página. Vuelve a intentarlo.", icon="⚠️")
    st.page_link("views/inicio.py", label="Volver al inicio", icon="↩")

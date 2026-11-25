"""Componentes visuales reutilizables."""
from __future__ import annotations

import base64
import html
from datetime import date
from pathlib import Path

import streamlit as st

import api_client as api
import utils

ASSETS = Path(__file__).resolve().parent.parent / "assets"


# ------------------------------------------------------------------ base
def cargar_estilos() -> None:
    st.html(f"<style>{(ASSETS / 'styles.css').read_text(encoding='utf-8')}</style>")


def cabecera(titulo: str, subtitulo: str | None = None) -> None:
    st.title(titulo)
    if subtitulo:
        st.html(f"<div class='eo-sub'>{html.escape(subtitulo)}</div>")


@st.cache_data
def _avatar_img(nombre: str) -> str:
    datos = base64.b64encode((ASSETS / nombre).read_bytes()).decode()
    return f"<img src='data:image/svg+xml;base64,{datos}' alt='Avatar' data-avatar='{nombre}'>"


def ficha_empleado_html(emp: dict, pequena: bool = False) -> str:
    return (
        f"<div class='eo-ficha{' peq' if pequena else ''}'>{_avatar_img(utils.archivo_avatar(emp.get('genero')))}"
        f"<div class='eo-nombre'>{html.escape(emp['nombre'])}</div>"
        f"<div class='eo-dato'>Turno {html.escape(emp['turno'])} · CI {emp['ci']}</div></div>"
    )


def estrellas_html(promedio: float | None) -> str:
    llenas, medias, vacias = utils.estrellas(promedio)
    return (
        "<span class='eo-estrellas' aria-label='" + utils.formato_numero(promedio) + " de 5'>"
        + "<span class='eo-estrella-llena'>★</span>" * llenas
        + "<span class='eo-estrella-media'>★</span>" * medias
        + "<span class='eo-estrella-vacia'>★</span>" * vacias
        + "</span>"
    )


def ranking_html(valor: float | None) -> str:
    texto = utils.formato_numero(valor, 1) if valor is not None else "Sin datos"
    return (
        f"<span class='eo-ranking'>{texto}{' / 10' if valor is not None else ''}</span>"
        f"<span class='eo-info' title='{html.escape(utils.TEXTO_INFO_RANKING)}'>ⓘ</span>"
    )


def tabla_html(columnas: list[str], filas: list[list[str]], estilos: list[list[str | None]] | None = None,
               clases_fila: list[str | None] | None = None) -> str:
    """Tabla HTML simple. estilos[i][j] = 'verde' | 'rojo' | None para la celda de datos j de la fila i."""
    cab = "".join(f"<th>{html.escape(c)}</th>" for c in columnas)
    cuerpo = []
    for i, fila in enumerate(filas):
        celdas = [f"<td>{html.escape(fila[0])}</td>"]
        for j, valor in enumerate(fila[1:]):
            color = estilos[i][j] if estilos else None
            estilo = f" style='background:{utils.FONDOS[color]};color:{utils.COLORES[color]};font-weight:600' data-color='{color}'" if color else ""
            celdas.append(f"<td{estilo}>{html.escape(valor)}</td>")
        clase = f" class='{clases_fila[i]}'" if clases_fila and clases_fila[i] else ""
        cuerpo.append(f"<tr{clase}>{''.join(celdas)}</tr>")
    return f"<table class='eo-tabla'><thead><tr>{cab}</tr></thead><tbody>{''.join(cuerpo)}</tbody></table>"


# ------------------------------------------------------------------ filtros
def filtro_periodo(key: str, desde: date | None = None, hasta: date | None = None) -> tuple[date, date] | None:
    defecto = utils.periodo_por_defecto()
    valor = st.date_input(
        "Periodo evaluado", value=(desde or defecto[0], hasta or defecto[1]), key=key, format="DD/MM/YYYY",
        help="Fecha de inicio y fecha de fin. Se tienen en cuenta evaluaciones, conflictos y ausencias dentro del periodo.",
    )
    periodo = utils.validar_periodo(valor)
    if periodo is None:
        st.warning("Selecciona un periodo completo y válido (fecha de inicio y fecha de fin).")
    return periodo


def buscador_empleado(empleados: list[dict], key: str, ci_inicial: int | None = None) -> dict | None:
    por_ci = {e["ci"]: e for e in empleados}
    opciones = list(por_ci)
    indice = opciones.index(ci_inicial) if ci_inicial in por_ci else None
    ci = st.selectbox(
        "Empleado", opciones, index=indice, key=key, placeholder="Buscar por nombre o CI…",
        format_func=lambda c: utils.etiqueta_empleado(por_ci[c]), filter_mode="contains",
    )
    return por_ci.get(ci)


# ------------------------------------------------------------------ errores
def mostrar_error(res: api.Resultado) -> None:
    """Muestra un error amigable con botón de reintento. Nunca muestra trazas."""
    if res.code in ("CONNECTION_ERROR", "TIMEOUT"):
        st.error(f"{res.message} Comprueba que el backend está arrancado e inténtalo de nuevo.", icon="⚠️")
    elif res.status and res.status >= 500 or res.code == "UNEXPECTED":
        st.error("No se pudo obtener la información por un error del servidor. Inténtalo de nuevo en unos segundos.", icon="⚠️")
    else:
        st.error(res.message or "No se pudo obtener la información.", icon="⚠️")
    if st.button("Reintentar", key=f"reintentar_{res.code}"):
        api.limpiar_cache()
        st.rerun()


def empleado_no_encontrado(ci) -> None:
    st.error(f"Empleado no encontrado (CI {html.escape(str(ci))}).", icon="🔎")
    st.page_link("views/inicio.py", label="Volver al inicio", icon="↩")


def cargar_empleados() -> list[dict]:
    res = api.listar_empleados()
    if not res.ok:
        mostrar_error(res)
        st.stop()
    if not res.data:
        st.info("No hay empleados cargados en la base de datos.")
        st.stop()
    return res.data

"""Lógica de presentación pura (sin Streamlit), testeable de forma aislada."""
from __future__ import annotations

from datetime import date, timedelta

DIAS_LABORABLES = 225
TEXTO_INFO_AUSENTISMO = (
    f"Se toman {DIAS_LABORABLES} días como total de días laborables. "
    "No incluye compensaciones por exceso de jornada o festivos."
)
TEXTO_INFO_RANKING = (
    "Ranking de 1 a 10 calculado con: promedio de aptitudes (70%), "
    "conflictos del Radar ponderados por gravedad (20%; leve 1, moderado 3, grave 5 puntos) "
    "y días de falta sin justificar (10%)."
)

COLORES = {"rojo": "#B3261E", "amarillo": "#C9A227", "verde": "#2E7D32"}
FONDOS = {"rojo": "#F6DEDC", "amarillo": "#F7EFD2", "verde": "#DCEEDC"}

TURNOS = ["Todos", "Mañana", "Tarde", "Noche"]
ORDENES = {
    "Ranking: de mejor a peor": "ranking_desc",
    "Ranking: de peor a mejor": "ranking_asc",
    "Turno: ascendente": "turno_asc",
    "Turno: descendente": "turno_desc",
}


def color_promedio(promedio: float | None) -> str | None:
    """1–2,99 rojo · 3–3,99 amarillo · 4–5 verde."""
    if promedio is None:
        return None
    if promedio < 3:
        return "rojo"
    if promedio < 4:
        return "amarillo"
    return "verde"


def estrellas(promedio: float | None, total: int = 5) -> tuple[int, int, int]:
    """(llenas, medias, vacías), redondeando al medio punto más cercano. 3,5 → (3, 1, 1)."""
    if promedio is None:
        return 0, 0, total
    redondeado = round(max(0.0, min(float(total), promedio)) * 2) / 2
    llenas = int(redondeado)
    medias = 1 if redondeado - llenas else 0
    return llenas, medias, total - llenas - medias


def archivo_avatar(genero: str | None) -> str:
    return {"M": "avatar_hombre.svg", "F": "avatar_mujer.svg"}.get(genero or "", "avatar_neutro.svg")


def etiqueta_empleado(emp: dict) -> str:
    return f"{emp['nombre']} ({emp['ci']})"


def formato_numero(valor: float | None, decimales: int = 2) -> str:
    if valor is None:
        return "—"
    return f"{valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def periodo_por_defecto(hoy: date | None = None) -> tuple[date, date]:
    hoy = hoy or date.today()
    return hoy - timedelta(days=365), hoy


def parse_fecha(valor: str | None) -> date | None:
    try:
        return date.fromisoformat(valor) if valor else None
    except ValueError:
        return None


def validar_periodo(valor) -> tuple[date, date] | None:
    """El date_input en modo rango devuelve una tupla de 0, 1 o 2 fechas mientras se elige."""
    if not isinstance(valor, (tuple, list)) or len(valor) != 2 or not all(valor):
        return None
    desde, hasta = valor
    return (desde, hasta) if desde <= hasta else None

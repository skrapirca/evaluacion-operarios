"""Configuración y parámetros de negocio. Todo lo ajustable está aquí."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def db_path() -> Path:
    """Ruta de la BBDD. Se lee en cada llamada para poder cambiarla en tests."""
    return Path(os.environ.get("DB_PATH", ROOT / "data" / "evaluaciones.db"))


# --- Dominio -----------------------------------------------------------------
APTITUDES = {
    1: "Operativa / Calidad",
    2: "Seguridad y orden",
    3: "Productividad y método",
    4: "Actitud y compromiso",
    5: "Equipo y conflicto",
}
ESCALA = {1: "Muy deficiente", 2: "Deficiente", 3: "Adecuado", 4: "Muy bueno", 5: "Excelente"}
GRAVEDADES = ["Leve", "Moderado", "Grave"]
TURNOS = ["Mañana", "Tarde", "Noche"]  # orden lógico usado al ordenar por turno

# --- Ausentismo ----------------------------------------------------------------
JORNADA_HORAS = 8
DIAS_LABORABLES = 225
MOTIVO_PENALIZA = "FALTA SIN JUSTIFICAR"
# Motivos que se muestran pero NO cuentan para el % de ausentismo.
MOTIVOS_EXCLUIDOS_AUSENTISMO = {"EXCESO JORNADA, COMPENSACIÓN FESTIVOS, ACUM., ETC"}

# --- Ranking 1-10 ---------------------------------------------------------------
PESO_APTITUDES = 0.7
PESO_CONFLICTOS = 0.2
PESO_AUSENCIAS = 0.1
PENALIZACION_GRAVEDAD = {"Leve": 1, "Moderado": 3, "Grave": 5}
# Puntos de penalización a partir de los cuales el componente de conflictos vale 0.
# El prompt proponía 10, pero con los datos reales (56-78 puntos por empleado) todos
# quedaban en 0 y el componente no diferenciaba a nadie. Con 100 sí lo hace.
TOPE_PENALIZACION_CONFLICTOS = 100
# Días de "Falta sin justificar" a partir de los cuales el componente de ausencias vale 0.
TOPE_DIAS_FALTA = 10

TEXTO_INFO_RANKING = (
    "Ranking de 1 a 10 calculado con: promedio de aptitudes (70%), "
    "conflictos del Radar ponderados por gravedad (20%; leve 1, moderado 3, grave 5 puntos) "
    "y días de falta sin justificar (10%)."
)
TEXTO_INFO_AUSENTISMO = (
    f"Se toman {DIAS_LABORABLES} días como total de días laborables. "
    "No incluye compensaciones por exceso de jornada o festivos."
)

# --- API -------------------------------------------------------------------------
MAX_RESULTADOS_BUSQUEDA = 10
MIN_COMPARACION, MAX_COMPARACION = 2, 5
ORDENES_RANKING = {"ranking_desc", "ranking_asc", "turno_asc", "turno_desc"}
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:8501")

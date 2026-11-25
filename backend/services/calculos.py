"""Lógica de cálculo pura (sin acceso a BBDD), testeable de forma aislada."""
from __future__ import annotations

import unicodedata
from collections import Counter
from statistics import mean
from typing import Iterable, Mapping

from backend import config


def normalizar_texto(texto: str | None) -> str:
    """Minúsculas, sin tildes y sin espacios sobrantes (para búsquedas)."""
    texto = (texto or "").strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def dias_desde_unidades(unidades: float, unidad_tiempo: str) -> float:
    """Convierte una ausencia a días. Hora → unidades / jornada; Día → sin transformar."""
    if unidades is None or unidades <= 0:
        raise ValueError("Las unidades deben ser mayores que 0")
    unidad = normalizar_texto(unidad_tiempo)
    if unidad in ("hora", "horas"):
        return round(unidades / config.JORNADA_HORAS, 4)
    if unidad in ("dia", "dias"):
        return float(unidades)
    raise ValueError(f"Unidad de tiempo no válida: {unidad_tiempo!r}")


def promedio(valores: Iterable[float | None]) -> float | None:
    vals = [v for v in valores if v is not None]
    return round(mean(vals), 2) if vals else None


def promedios_por_aptitud(evaluaciones: Iterable[Mapping]) -> dict[int, float | None]:
    """evaluaciones: filas con 'aptitud' y 'puntaje'. Devuelve {aptitud: promedio | None}."""
    por_apt: dict[int, list[int]] = {a: [] for a in config.APTITUDES}
    for e in evaluaciones:
        por_apt[e["aptitud"]].append(e["puntaje"])
    return {a: promedio(v) for a, v in por_apt.items()}


def promedio_general(prom_aptitudes: Mapping[int, float | None]) -> float | None:
    return promedio(prom_aptitudes.values())


def contar_gravedades(gravedades: Iterable[str]) -> dict[str, int]:
    c = Counter(gravedades)
    return {g: c.get(g, 0) for g in config.GRAVEDADES}


def penalizacion_conflictos(conteo: Mapping[str, int]) -> int:
    return sum(config.PENALIZACION_GRAVEDAD[g] * conteo.get(g, 0) for g in config.GRAVEDADES)


def componente_aptitudes(prom_general: float) -> float:
    return (prom_general - 1) / 4


def componente_conflictos(conteo: Mapping[str, int]) -> float:
    return max(0.0, 1 - penalizacion_conflictos(conteo) / config.TOPE_PENALIZACION_CONFLICTOS)


def componente_ausencias(dias_falta_sin_justificar: float) -> float:
    return max(0.0, 1 - dias_falta_sin_justificar / config.TOPE_DIAS_FALTA)


def calcular_ranking(prom_general: float | None, conteo: Mapping[str, int], dias_falta: float) -> float | None:
    """Ranking 1-10. Sin evaluaciones en el periodo → None ("Sin datos")."""
    if prom_general is None:
        return None
    total = (
        config.PESO_APTITUDES * componente_aptitudes(prom_general)
        + config.PESO_CONFLICTOS * componente_conflictos(conteo)
        + config.PESO_AUSENCIAS * componente_ausencias(dias_falta)
    )
    return round(1 + 9 * total, 1)


def porcentaje_ausentismo(dias: float) -> float:
    return round(dias / config.DIAS_LABORABLES * 100, 2)


def computa_ausentismo(motivo: str) -> bool:
    return motivo not in config.MOTIVOS_EXCLUIDOS_AUSENTISMO


def es_falta_sin_justificar(motivo: str) -> bool:
    return normalizar_texto(motivo) == normalizar_texto(config.MOTIVO_PENALIZA)


def colores_comparacion(valores: Mapping, mayor_es_mejor: bool = True) -> dict:
    """Devuelve {clave: 'verde' | 'rojo' | None}.

    Verde para el mejor valor y rojo para el peor; los empates se colorean todos.
    Si todos los valores son iguales (o hay menos de 2 con dato), no se colorea nada.
    """
    con_dato = {k: v for k, v in valores.items() if v is not None}
    resultado = {k: None for k in valores}
    if len(con_dato) < 2 or len(set(con_dato.values())) == 1:
        return resultado
    mejor = max(con_dato.values()) if mayor_es_mejor else min(con_dato.values())
    peor = min(con_dato.values()) if mayor_es_mejor else max(con_dato.values())
    for k, v in con_dato.items():
        if v == mejor:
            resultado[k] = "verde"
        elif v == peor:
            resultado[k] = "rojo"
    return resultado


def colores_radar(conteos: Mapping[object, Mapping[str, int]]) -> dict:
    """Mejor = menos graves; a igualdad, menos moderados; luego menos leves."""
    claves = {k: (c.get("Grave", 0), c.get("Moderado", 0), c.get("Leve", 0)) for k, c in conteos.items()}
    return colores_comparacion(claves, mayor_es_mejor=False)


def resumen_observaciones(evaluaciones: list[Mapping]) -> str:
    """Resumen por reglas de las observaciones de UNA aptitud."""
    if not evaluaciones:
        return "Sin evaluaciones en el periodo."
    alta = max(evaluaciones, key=lambda e: e["puntaje"])
    baja = min(evaluaciones, key=lambda e: e["puntaje"])
    if alta["puntaje"] == baja["puntaje"]:
        textos = list(dict.fromkeys(e["observacion"] for e in evaluaciones))
        return f"Valoración homogénea ({alta['puntaje']} - {config.ESCALA[alta['puntaje']]}). " + " · ".join(
            f"«{t}»" for t in textos[:3]
        )
    return (
        f"Mejor valoración ({alta['puntaje']}, {alta['evaluador']}): «{alta['observacion'].rstrip('.')}». "
        f"Peor valoración ({baja['puntaje']}, {baja['evaluador']}): «{baja['observacion'].rstrip('.')}»."
    )


def resumen_radar(conflictos: list[Mapping]) -> str:
    if not conflictos:
        return "Sin conflictos registrados en el periodo."
    n = len(conflictos)
    g = contar_gravedades(c["gravedad"] for c in conflictos)
    tipo, n_tipo = Counter(c["tipo_incidencia"] for c in conflictos).most_common(1)[0]
    partes = [
        f"{n} incidencias: {g['Leve']} leves, {g['Moderado']} moderadas y {g['Grave']} graves.",
        f"Tipo más frecuente: {tipo} ({n_tipo}).",
    ]
    areas = Counter(c["area"] for c in conflictos if c.get("area"))
    if areas:
        area, n_area = areas.most_common(1)[0]
        partes.append(f"Área más frecuente: {area} ({n_area}).")
    reacc = [c.get("reaccion_trabajador") for c in conflictos if c.get("reaccion_trabajador")]
    if reacc:
        rectifica = sum(1 for r in reacc if normalizar_texto(r).startswith("ha rectificado"))
        partes.append(f"Rectificó su conducta en {rectifica} de {len(reacc)} casos.")
    return " ".join(partes)

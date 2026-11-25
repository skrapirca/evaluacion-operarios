"""Validación de parámetros comunes."""
from datetime import date

from backend import config
from backend.errors import ApiError


def _parse_fecha(valor: str | None, nombre: str) -> date | None:
    if valor is None or valor == "":
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ApiError(400, "INVALID_DATE_RANGE", f"Fecha '{nombre}' no válida: use el formato AAAA-MM-DD.", {nombre: valor})


def periodo(desde: str | None, hasta: str | None) -> tuple[date | None, date | None]:
    d, h = _parse_fecha(desde, "desde"), _parse_fecha(hasta, "hasta")
    if d and h and d > h:
        raise ApiError(400, "INVALID_DATE_RANGE", "La fecha de inicio no puede ser posterior a la fecha de fin.",
                       {"desde": desde, "hasta": hasta})
    return d, h


def lista_cis(cis: str) -> list[int]:
    partes = [p.strip() for p in cis.split(",") if p.strip()]
    try:
        valores = [int(p) for p in partes]
    except ValueError:
        raise ApiError(400, "INVALID_PARAMETER", "Los CI deben ser números separados por comas.", {"cis": cis})
    if len(set(valores)) != len(valores):
        raise ApiError(400, "INVALID_COMPARISON_SIZE", "Hay CI duplicados en la comparación.", {"cis": valores})
    if not config.MIN_COMPARACION <= len(valores) <= config.MAX_COMPARACION:
        raise ApiError(400, "INVALID_COMPARISON_SIZE",
                       f"Se pueden comparar entre {config.MIN_COMPARACION} y {config.MAX_COMPARACION} empleados.",
                       {"recibidos": len(valores)})
    return valores


def turno(valor: str) -> str:
    if valor.lower() == "todos":
        return "todos"
    for t in config.TURNOS:
        if valor.lower() == t.lower() or (valor.lower() == "manana" and t == "Mañana"):
            return t
    raise ApiError(400, "INVALID_PARAMETER", f"Turno no válido: {valor}. Valores: todos, {', '.join(config.TURNOS)}.", {"turno": valor})


def orden(valor: str) -> str:
    if valor not in config.ORDENES_RANKING:
        raise ApiError(400, "INVALID_PARAMETER", f"Orden no válido: {valor}.", {"orden": valor, "validos": sorted(config.ORDENES_RANKING)})
    return valor

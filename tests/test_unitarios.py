"""5.1 Tests unitarios de la lógica de cálculo (backend) y de presentación (frontend)."""
import pytest

import utils
from backend.services import calculos as calc


# U01-U03
@pytest.mark.parametrize("unidades, unidad, esperado", [(4, "Hora", 0.5), (8, "Horas", 1.0), (2, "Día", 2.0), (2, "Días", 2.0)])
def test_u01_u03_conversion_a_dias(unidades, unidad, esperado):
    assert calc.dias_desde_unidades(unidades, unidad) == esperado


@pytest.mark.parametrize("unidades, unidad", [(0, "Hora"), (-1, "Día"), (2, "Semana")])
def test_conversion_invalida(unidades, unidad):
    with pytest.raises(ValueError):
        calc.dias_desde_unidades(unidades, unidad)


def test_u04_promedio():
    assert calc.promedio([3, 4, 5]) == 4.00
    assert calc.promedio([]) is None


@pytest.mark.parametrize("valor, color", [(2.99, "rojo"), (3.00, "amarillo"), (3.99, "amarillo"), (4.00, "verde"), (1, "rojo"), (5, "verde"), (None, None)])
def test_u05_color_promedio(valor, color):
    assert utils.color_promedio(valor) == color


@pytest.mark.parametrize("valor, esperado", [(3.5, (3, 1, 1)), (5, (5, 0, 0)), (1, (1, 0, 4)), (2.67, (2, 1, 2)), (None, (0, 0, 5))])
def test_u06_estrellas(valor, esperado):
    assert utils.estrellas(valor) == esperado


def test_u07_ranking_maximo():
    assert calc.calcular_ranking(5, {"Leve": 0, "Moderado": 0, "Grave": 0}, 0) == 10.0


def test_u08_ranking_minimo():
    assert calc.calcular_ranking(1, {"Grave": 20}, 10) == 1.0


def test_u09_solo_penaliza_falta_sin_justificar():
    assert calc.es_falta_sin_justificar("FALTA SIN JUSTIFICAR")
    assert calc.es_falta_sin_justificar("Falta sin justificar ")
    assert not calc.es_falta_sin_justificar("FALTA JUSTIFICADA - ENFERMEDAD SIN AUTORIZACIÓN")
    assert not calc.es_falta_sin_justificar("ENFERMEDAD CON BAJA")


def test_u10_porcentaje_ausentismo():
    assert calc.porcentaje_ausentismo(22.5) == 10.0


def test_u10b_exceso_jornada_no_computa():
    assert not calc.computa_ausentismo("EXCESO JORNADA, COMPENSACIÓN FESTIVOS, ACUM., ETC")
    assert calc.computa_ausentismo("ENFERMEDAD CON BAJA")


def test_u11_sin_evaluaciones_sin_ranking():
    assert calc.calcular_ranking(None, {}, 0) is None


@pytest.mark.parametrize("genero, archivo", [("M", "avatar_hombre.svg"), ("F", "avatar_mujer.svg"), (None, "avatar_neutro.svg")])
def test_u12_avatar_segun_genero(genero, archivo):
    assert utils.archivo_avatar(genero) == archivo


def test_u13_empate_en_maximo():
    assert calc.colores_comparacion({"a": 4, "b": 4, "c": 2}) == {"a": "verde", "b": "verde", "c": "rojo"}


def test_u14_todos_iguales_sin_color():
    assert calc.colores_comparacion({"a": 3, "b": 3}) == {"a": None, "b": None}


def test_colores_radar_menos_graves_es_mejor():
    colores = calc.colores_radar({
        "a": {"Leve": 10, "Moderado": 0, "Grave": 0},
        "b": {"Leve": 0, "Moderado": 0, "Grave": 1},
        "c": {"Leve": 0, "Moderado": 2, "Grave": 0},
    })
    assert colores == {"a": "verde", "b": "rojo", "c": None}


def test_normalizar_texto():
    assert calc.normalizar_texto("  IRÉ ") == "ire"


def test_validar_periodo():
    from datetime import date
    assert utils.validar_periodo((date(2026, 1, 1),)) is None
    assert utils.validar_periodo((date(2026, 2, 1), date(2026, 1, 1))) is None
    assert utils.validar_periodo((date(2026, 1, 1), date(2026, 2, 1))) == (date(2026, 1, 1), date(2026, 2, 1))

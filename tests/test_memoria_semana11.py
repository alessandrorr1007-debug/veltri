"""Pruebas locales de los contratos de memoria, sin depender de un modelo."""

import json

import pytest

from src.academic.memoria_semana11 import (
    RUTA_HALLAZGOS,
    evidencia_canonica,
    verificar_archivo,
    verificar_lectura,
)

EVIDENCIA = {"sintetico": True, "requiere_revision": True, "efecto_comercial": False}
CANONICO = json.dumps(EVIDENCIA, sort_keys=True, separators=(",", ":"))


def test_canonicaliza_texto_y_bloques():
    assert evidencia_canonica(json.dumps(EVIDENCIA)) == CANONICO
    assert evidencia_canonica([{"type": "text", "text": CANONICO}]) == CANONICO


@pytest.mark.parametrize("cambio", [
    {"efecto_comercial": True}, {"sintetico": False}, {"requiere_revision": False},
    {"sintetico": 1}, {"dato_extra": "no permitido"},
])
def test_rechaza_evidencia_fuera_del_contrato(cambio):
    with pytest.raises(ValueError, match="evidencia_academica_invalida"):
        evidencia_canonica(json.dumps({**EVIDENCIA, **cambio}))


def test_lectura_debe_contener_evidencia():
    assert verificar_lectura("1\t" + CANONICO, CANONICO) == CANONICO
    with pytest.raises(ValueError, match="lectura_academica_no_coincide"):
        verificar_lectura("archivo vacío", CANONICO)


def test_estado_retiene_archivo_virtual():
    assert verificar_archivo({RUTA_HALLAZGOS: {"content": [CANONICO]}}, CANONICO) == CANONICO
    with pytest.raises(ValueError, match="artefacto_academico_ausente"):
        verificar_archivo({}, CANONICO)


def test_rechaza_archivo_adulterado():
    archivo = {RUTA_HALLAZGOS: {"content": ['{"efecto_comercial":true}']}}
    with pytest.raises(ValueError, match="evidencia_academica_invalida"):
        verificar_archivo(archivo, CANONICO)

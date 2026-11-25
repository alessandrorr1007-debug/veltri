"""Aceptación determinista del TCO, la rentabilidad y los supuestos en PEN."""

import json
import subprocess
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from src.economia import (
    PERFIL,
    Costo,
    Supuestos,
    calcular,
    generar_informe,
    payback,
    punto_equilibrio,
    roi,
    van,
)

D = Decimal


@pytest.fixture
def perfil():
    return json.loads(PERFIL.read_text(encoding="utf-8"))


def _datos_base(perfil):
    empresa = perfil["empresarial"]
    return Supuestos(**empresa["supuestos"]), [Costo(**p) for p in empresa["costos"]]


def test_tco_36_meses_separa_labor_soporte_inversion_y_compartidos(perfil):
    resultado = generar_informe(perfil)["empresarial"]["base"]
    asis, tobe = (resultado["tco"][flujo] for flujo in ("asis", "tobe"))
    assert asis["inicial_pen"] == 0
    assert asis["soporte_mensual_pen"] == 70
    assert tobe["soporte_mensual_pen"] == D("402.20")
    assert asis["labor_mensual_pen"] == D("2058.24")
    assert tobe["labor_mensual_pen"] == D("1038.72")
    assert resultado["operacion_incremental_mes_pen"] == D("332.20")
    assert asis["acumulado_por_anio_pen"] == [D("25538.88"), D("51077.76"), D("76616.64")]
    assert tobe["acumulado_por_anio_pen"] == [D("22071.04"), D("39362.08"), D("56653.12")]
    assert asis["total_36_pen"] == D("76616.64")
    assert tobe["total_36_pen"] == D("56653.12")


def test_beneficios_flujos_y_roi_no_cuentan_dos_veces_el_ahorro_laboral(perfil):
    resultado = generar_informe(perfil)["empresarial"]["base"]
    assert resultado["horas_liberadas_mes"] == D("42.48")
    assert resultado["bruto_economico_mes_pen"] == D("1019.52")
    assert resultado["realizable_mes_pen"] == D("611.712")
    assert resultado["neto_mes_pen"] == D("279.512")
    assert resultado["flujo_anual_pen"] == [D("-4780"), *([D("3354.144")] * 3)]
    assert len(resultado["flujo_acumulado_mensual_pen"]) == 37
    assert resultado["flujo_acumulado_mensual_pen"][-1] == D("5282.432")
    assert resultado["neto_36_pen"] == D("5282.432")
    assert resultado["roi_anio_1_pct"].quantize(D(".01")) == D("-16.27")
    assert resultado["roi_estable_anual_pct"].quantize(D(".01")) == D("84.14")
    assert resultado["roi_36_pct"].quantize(D(".01")) == D("31.56")
    assert resultado["capacidad_adicional_consultas_mes"] == 235
    assert resultado["van_pen"].quantize(D(".01")) == D("3276.09")


def test_van_descuenta_flujos_anuales_y_mantiene_inversion_inmediata():
    flujos = [D("-400"), D("112"), D("125.44"), D("140.4928")]
    assert van(flujos, D(".12")) == D("-100")
    assert van(flujos, D("0")) == sum(flujos)
    assert van([D("-100"), D("-12"), D("0"), D("0")], D(".20")) == D("-110")


def test_payback_usa_acumulacion_mensual_con_flujos_negativos_e_interpolacion():
    assert payback(D(100), [D(-50), D(100), D(100)]) == {
        "estado": "recuperado", "meses": D("2.5"),
    }
    assert payback(D(10), [D("-1")] * 36) == {
        "estado": "sin_recuperacion_en_horizonte", "meses": None,
    }
    assert payback(D(36), [D(1)] * 36) == {"estado": "recuperado", "meses": D(36)}
    assert payback(D(37), [D(1)] * 36)["meses"] is None


def test_inversion_y_denominador_cero_no_generan_indicadores_falsos(perfil):
    base, _ = _datos_base(perfil)
    resultado = calcular(base, [], D(".12"))
    assert resultado["inversion_incremental_pen"] == 0
    assert resultado["payback"] == {"estado": "sin_inversion_incremental", "meses": None}
    assert resultado["roi_anio_1_pct"] is None
    assert resultado["roi_estable_anual_pct"] is None
    assert resultado["roi_36_pct"] is None
    assert roi(D(100), D(50)) == 100
    assert roi(D(100), D(-1)) is None


def test_equilibrio_discreto_van_y_operacion_con_validacion_de_vecinos(perfil):
    base, costos = _datos_base(perfil)
    resultado = calcular(base, costos, D(".12"))
    assert resultado["equilibrio_operativo_consultas_mes"] == 131
    assert resultado["equilibrio_36_consultas_mes"] == 183
    assert resultado["equilibrio_van_consultas_mes"] == 196
    for campo, resultado_pen in (
        ("equilibrio_operativo_consultas_mes", "neto_mes_pen"),
        ("equilibrio_36_consultas_mes", "neto_36_pen"),
        ("equilibrio_van_consultas_mes", "van_pen"),
    ):
        minimo = resultado[campo]
        assert calcular(replace(base, consultas_mes=minimo), costos, D(".12"))[resultado_pen] >= 0
        anterior = calcular(replace(base, consultas_mes=minimo - 1), costos, D(".12"))
        assert anterior[resultado_pen] < 0
    assert punto_equilibrio(D(20), D(5)) == 4
    assert punto_equilibrio(D(20), D(0)) is None
    assert punto_equilibrio(D(20), D(-5)) is None
    perjudicial = calcular(replace(base, minutos_tobe=D(60)), costos, D(".12"))
    assert perjudicial["bruto_economico_mes_pen"] < 0
    assert perjudicial["equilibrio_van_consultas_mes"] is None
    assert perjudicial["payback"]["estado"] == "sin_recuperacion_en_horizonte"


def test_escenarios_independientes_y_sensibilidad_no_fuerzan_viabilidad(perfil):
    informe = generar_informe(perfil)
    assert informe["moneda"] == "PEN" and informe["meses"] == 36
    academico = informe["academico"]
    assert informe["supuestos_pendientes_revision"] is True
    assert academico["naturaleza"] == "estimacion_de_recursos_imputados"
    assert academico["realizable_mes_pen"] == 0
    assert academico["tco"]["tobe"]["total_36_pen"] == D(6261)
    empresa = informe["empresarial"]
    assert all(s["naturaleza"] == "proyeccion_hipotetica" for s in empresa.values())
    assert empresa["pesimista"]["van_pen"] < 0 < empresa["base"]["van_pen"]
    assert empresa["pesimista"]["payback"]["meses"] is None
    assert empresa["optimista"]["van_pen"] > empresa["base"]["van_pen"]
    cambios = informe["sensibilidad_empresarial"]
    assert len(cambios) == 14
    por_variable = {}
    for fila in cambios:
        por_variable.setdefault(fila["variable"], []).append(fila["van_pen"])
    assert set(por_variable) == {
        "consultas_mes", "minutos_ahorrados_rutina", "costo_hora_pen", "factor_operacion",
        "factor_inicial", "tasa_descuento_anual", "proporcion_hitl",
    }
    for variable in ("consultas_mes", "minutos_ahorrados_rutina", "costo_hora_pen"):
        abajo, arriba = por_variable[variable]
        assert abajo < empresa["base"]["van_pen"] < arriba
    for variable in (
        "factor_operacion", "factor_inicial", "tasa_descuento_anual", "proporcion_hitl",
    ):
        abajo, arriba = por_variable[variable]
        assert arriba < empresa["base"]["van_pen"] < abajo


@pytest.mark.parametrize(("campo", "valor"), [
    ("consultas_mes", True), ("consultas_mes", -1), ("minutos_asis", 1.2),
    ("minutos_tobe", "-2"), ("proporcion_hitl", "35"), ("costo_hora_pen", "NaN"),
    ("realizacion", D("Infinity")),
])
def test_rechaza_unidades_y_entradas_invalidas(perfil, campo, valor):
    datos = perfil["empresarial"]["supuestos"]
    with pytest.raises(ValueError, match=campo):
        Supuestos(**{**datos, campo: valor})


def test_rechaza_moneda_distinta_costos_duplicados_y_periodos_ambiguos(perfil):
    with pytest.raises(ValueError, match="PEN"):
        generar_informe({**perfil, "moneda": "USD"})
    with pytest.raises(ValueError, match="desconocidos"):
        generar_informe({**perfil, "meses": 12})
    with pytest.raises(ValueError, match="tasa"):
        generar_informe({**perfil, "tasa_descuento_anual": "12"})
    base, costos = _datos_base(perfil)
    with pytest.raises(ValueError, match="únicos"):
        calcular(base, [*costos, costos[0]], D(".12"))
    with pytest.raises(ValueError, match="periodo"):
        replace(costos[0], periodo="anual")
    with pytest.raises(ValueError, match="unidad"):
        replace(costos[0], unidad="minutos")


def test_modulo_local_publica_resultados_reutilizables_en_json():
    raiz = Path(__file__).resolve().parents[1]
    proceso = subprocess.run(
        [sys.executable, "-m", "src.economia"], cwd=raiz, capture_output=True,
        encoding="utf-8", timeout=10, check=False,
    )
    assert proceso.returncode == 0, proceso.stderr
    resultado = json.loads(proceso.stdout)
    assert resultado["moneda"] == "PEN"
    assert D(resultado["empresarial"]["base"]["van_pen"]).quantize(D(".01")) == D("3276.09")

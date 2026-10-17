"""Integridad del catálogo sintético y sus relaciones, sin lógica de negocio."""

import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
CAT = json.loads((RAIZ / "data/catalogo.json").read_text(encoding="utf-8"))
COMP = json.loads((RAIZ / "data/compatibilidad.json").read_text(encoding="utf-8"))
PRODUCTOS = CAT["productos"]
POR_SKU = {p["sku"]: p for p in PRODUCTOS}
CAMPOS = {
    "cpu": ["socket", "potencia_diseno_w"],
    "placa": ["socket", "chipset", "ram_tipo", "formato", "ranuras_ram", "ram_max_gb",
              "interfaces_ssd", "bios_requiere_verificacion"],
    "gpu": ["potencia_diseno_w", "longitud_mm", "conectores_requeridos"],
    "ram": ["ram_tipo", "capacidad_total_gb", "modulos", "velocidad_mt_s"],
    "ssd": ["capacidad_gb", "interfaz", "generacion_pcie", "formato"],
    "fuente": ["potencia_nominal_w", "formato", "conectores"],
    "gabinete": ["formatos_placa", "formatos_fuente", "gpu_max_mm", "cooler_max_mm"],
    "refrigeracion": ["sockets", "altura_mm", "capacidad_diseno_w"],
}


def test_identificadores_y_cobertura():
    assert 80 <= len(PRODUCTOS) <= 90
    assert len(POR_SKU) == len(PRODUCTOS)
    assert {p["categoria"] for p in PRODUCTOS} == set(CAMPOS)
    assert {p["especificaciones"]["socket"] for p in PRODUCTOS
            if p["categoria"] == "cpu"} == {"AM4", "AM5", "LGA1700"}
    assert {p["especificaciones"]["ram_tipo"] for p in PRODUCTOS
            if p["categoria"] == "ram"} == {"DDR4", "DDR5"}
    assert len({p["stock"] for p in PRODUCTOS}) > 1


@pytest.mark.parametrize("producto", PRODUCTOS, ids=lambda p: p["sku"])
def test_producto_valido(producto):
    assert producto["sku"] and producto["nombre"]
    assert producto["sku"].isascii() and producto["sku"] == producto["sku"].upper()
    for campo in ("precio_centimos", "stock"):
        assert type(producto[campo]) is int
    assert producto["precio_centimos"] > 0
    assert producto["stock"] >= 0
    spec = producto["especificaciones"]
    assert set(CAMPOS[producto["categoria"]]) <= spec.keys()
    for key, value in spec.items():
        if key.endswith(("_w", "_mm", "_gb", "_mt_s")) or key in ("modulos", "ranuras_ram"):
            assert type(value) is int and value > 0
    for campo in ("conectores", "conectores_requeridos"):
        if campo in spec:
            assert all(type(v) is int and v > 0 for v in spec[campo].values())
    if "socket" in spec:
        assert spec["socket"] in COMP["sockets"]
    if producto["categoria"] == "placa":
        plataforma = COMP["sockets"][spec["socket"]]
        assert spec["chipset"] in plataforma["chipsets"]
        assert spec["ram_tipo"] in plataforma["ram_tipos"]
    if producto["categoria"] == "refrigeracion":
        assert set(spec["sockets"]) <= COMP["sockets"].keys()


def test_referencias_cpu_placa_completas_sin_duplicados():
    pares = []
    for relacion in COMP["relaciones_cpu_placa"]:
        cpu, placa = POR_SKU[relacion["cpu_sku"]], POR_SKU[relacion["placa_sku"]]
        assert cpu["categoria"] == "cpu" and placa["categoria"] == "placa"
        assert cpu["especificaciones"]["socket"] == placa["especificaciones"]["socket"]
        assert relacion["estado"] == "requiere_verificacion" and relacion["motivo"]
        pares.append((cpu["sku"], placa["sku"]))
    esperados = {(c["sku"], p["sku"]) for c in PRODUCTOS for p in PRODUCTOS
                 if c["categoria"] == "cpu" and p["categoria"] == "placa"
                 and c["especificaciones"]["socket"] == p["especificaciones"]["socket"]}
    assert len(pares) == len(set(pares))
    assert set(pares) == esperados


def test_caso_dorado_agotado():
    assert POR_SKU["CPU-AMD-5500"]["stock"] == 0
    casos = json.loads((RAIZ / "evals/casos_dorados.json").read_text(encoding="utf-8"))
    caso = next(c for c in casos["casos"] if c["id"] == "CP-3")
    assert "CPU-AMD-5500" in caso["esperado"]["motivo_menciona"]


def test_supuestos_explicitos():
    for datos in (CAT, COMP):
        assert datos["naturaleza"] == "demostracion_sintetica"
        assert datos["moneda"] == "PEN" and datos["version_esquema"] == "1.0"
        assert datos["aviso"]
    assert COMP["potencia"]["estado"] == "propuesta"
    assert type(COMP["potencia"]["reserva_componentes_w"]) is int
    assert COMP["potencia"]["reserva_componentes_w"] >= 0
    assert 0 < COMP["potencia"]["margen_porcentaje"] < 100
    assert COMP["evidencia"]["fabricante_verificado"] is False
    assert COMP["evidencia"]["faltante_o_incompatible"] == "revision_humana"
    assert COMP["ram"]["mezclar_generaciones"] is False

"""Casos de herramientas puras y bloqueos con datos de demo, sin LLM ni red."""

import hashlib
import json
from copy import deepcopy

import pytest

from src.tools.armador import armar
from src.tools.catalogo import Catalogo
from src.tools.cotizacion import cotizar
from src.tools.hardware import potencia_requerida, validar_configuracion
from src.tools.inventario import alternativas, comprobar_stock
from src.tools.pagos import comparar_pago
from src.tools.pedidos import RegistroDemo, clave_pedido


@pytest.fixture
def catalogo():
    return Catalogo()


@pytest.fixture
def seleccion():
    return dict.fromkeys(["CPU-AMD-5600", "MB-A520-DDR4", "GPU-RX6600",
                          "RAM-DDR4-8-2666", "SSD-NVME-500-G3", "PSU-450",
                          "CASE-01", "COOL-02"], 1)


def test_lectura_es_aislada_y_ordenada(catalogo):
    producto = catalogo.obtener("CPU-AMD-5500")
    producto["stock"] = 100
    assert catalogo.obtener("CPU-AMD-5500")["stock"] == 0
    assert [p["sku"] for p in catalogo.listar()] == sorted(p["sku"]
                                                        for p in catalogo.listar())


@pytest.mark.parametrize("cantidad", [True, 1.5, "2", 0, -1])
def test_rechaza_cantidades_invalidas(catalogo, cantidad):
    with pytest.raises(ValueError):
        cotizar(catalogo, {"CPU-AMD-5600": cantidad})


def test_rechaza_sku_desconocido_y_seleccion_vacia(catalogo):
    with pytest.raises(ValueError):
        catalogo.lineas({"NO-EXISTE": 1})
    with pytest.raises(ValueError):
        catalogo.lineas({})


def test_loader_rechaza_sku_duplicado(catalogo, tmp_path):
    productos = catalogo.listar()
    (tmp_path / "catalogo.json").write_text(json.dumps(
        {"moneda": "PEN", "productos": productos + [productos[0]]}), encoding="utf-8")
    (tmp_path / "compatibilidad.json").write_text(json.dumps(catalogo.reglas), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicado"):
        Catalogo(tmp_path)


def test_cp3_sin_stock_con_alternativa_y_fuente(catalogo):
    resultado = comprobar_stock(catalogo, {"CPU-AMD-5500": 1})
    assert resultado["hitl_requerido"] and not resultado["disponible"]
    assert resultado["faltantes"][0]["sku"] == "CPU-AMD-5500"
    assert resultado["fuente"] == "data/catalogo.json"
    sugerencias = alternativas(catalogo, "CPU-AMD-5500")
    assert sugerencias and "CPU-AMD-5500" not in sugerencias
    assert all(catalogo.obtener(s)["especificaciones"]["socket"] == "AM4"
               for s in sugerencias)


def test_stock_exactamente_disponible_y_exceso(catalogo):
    p = catalogo.obtener("CPU-AMD-5600")
    assert comprobar_stock(catalogo, {p["sku"]: p["stock"]})["disponible"]
    assert not comprobar_stock(catalogo, {p["sku"]: p["stock"] + 1})["disponible"]


def test_total_por_cantidad_sin_float_ni_impuesto(catalogo):
    resultado = cotizar(catalogo, {"CPU-AMD-5600": 2})
    assert resultado["total_centimos"] == 94000
    assert resultado["lineas"][0]["fuente"] == "data/catalogo.json#CPU-AMD-5600"
    assert not resultado["genera_proforma"]


def test_limite_presupuesto_inclusivo(catalogo, seleccion):
    total = cotizar(catalogo, seleccion)["total_centimos"]
    assert not cotizar(catalogo, seleccion, total)["sobre_presupuesto"]
    sobre = cotizar(catalogo, seleccion, total - 1)
    assert sobre["sobre_presupuesto"] and sobre["hitl_requerido"]
    assert "sobre_presupuesto" in sobre["bloqueos"]
    assert not sobre["genera_proforma"]


def test_compatible_en_datos_no_es_aprobacion_real(catalogo, seleccion):
    resultado = validar_configuracion(catalogo, seleccion)
    assert resultado["sin_conflictos_datos"]
    assert resultado["potencia_estimada_w"] == 444
    assert not resultado["aprobado_tecnicamente"] and resultado["hitl_requerido"]
    assert "verificar_soporte_cpu_bios" in resultado["pendientes"]


@pytest.mark.parametrize("anterior,nuevo,motivo", [
    ("CPU-AMD-5600", "CPU-AMD-7600", "socket_incompatible"),
    ("RAM-DDR4-8-2666", "RAM-DDR5-8-4800", "ram_incompatible"),
    ("GPU-RX6600", "GPU-RTX4080SUPER", "fuente_insuficiente"),
    ("GPU-RX6600", "GPU-RTX4080SUPER", "gpu_no_cabe"),
    ("CPU-AMD-5600", "CPU-INTEL-12400F", "cooler_insuficiente"),
])
def test_detecta_conflictos(catalogo, seleccion, anterior, nuevo, motivo):
    seleccion.pop(anterior)
    seleccion[nuevo] = 1
    resultado = validar_configuracion(catalogo, seleccion)
    assert motivo in resultado["conflictos"]
    assert not resultado["sin_conflictos_datos"] and resultado["hitl_requerido"]


@pytest.mark.parametrize("categoria,campo,valor,motivo", [
    ("placa", "ram_max_gb", 4, "ram_excede_capacidad"),
    ("placa", "ranuras_ram", 0, "ram_excede_ranuras"),
    ("placa", "interfaces_ssd", [], "ssd_incompatible"),
    ("placa", "chipset", "DESCONOCIDO", "chipset_incompatible"),
    ("refrigeracion", "sockets", [], "cooler_socket_incompatible"),
    ("refrigeracion", "altura_mm", 999, "cooler_no_cabe"),
    ("fuente", "conectores", {}, "conectores_insuficientes"),
    ("gabinete", "formatos_placa", [], "placa_no_cabe"),
    ("gabinete", "formatos_fuente", [], "fuente_no_cabe"),
])
def test_restricciones_independientes(catalogo, seleccion, categoria, campo, valor, motivo):
    # Ficha alterada solo en la instantánea de prueba, nunca en los archivos de datos.
    sku = next(s for s in seleccion if catalogo.obtener(s)["categoria"] == categoria)
    catalogo._productos[sku]["especificaciones"][campo] = valor
    assert motivo in validar_configuracion(catalogo, seleccion)["conflictos"]


def test_configuracion_incompleta_y_cantidad_duplicada(catalogo, seleccion):
    seleccion["CPU-AMD-5600"] = 2
    assert not validar_configuracion(catalogo, seleccion)["sin_conflictos_datos"]
    seleccion.pop("CPU-AMD-5600")
    assert "requiere_un_componente:cpu" in validar_configuracion(
        catalogo, seleccion)["conflictos"]


def test_estimacion_redondea_hacia_arriba_sin_float():
    assert potencia_requerida(105, 150, 100, 25) == 444
    assert potencia_requerida(100, 100, 100, 25) == 375
    assert potencia_requerida(10**18, 0, 0, 25) == 1250000000000000000
    with pytest.raises(ValueError):
        potencia_requerida(True, 0, 100, 25)


@pytest.mark.parametrize("monto,moneda,coincide,diferencia", [
    (9999, "PEN", False, -1), (10001, "PEN", False, 1),
    (10000, "PEN", True, 0), (10000, "USD", False, None),
    (0, "PEN", False, -10000),
])
def test_pago_nunca_se_acredita_solo_por_importe(monto, moneda, coincide, diferencia):
    pago = comparar_pago(10000, monto, moneda)
    assert pago["montos_coinciden"] is coincide
    assert pago["diferencia_centimos"] == diferencia
    assert pago["estado"] == "no_conciliado" and pago["hitl_requerido"]


def test_cp6_idempotencia_canonica_y_sin_datos_personales(catalogo, seleccion):
    antes = deepcopy(seleccion)
    registro = RegistroDemo()
    primero = registro.registrar("demo_cliente", seleccion, "web", catalogo)
    segundo = registro.registrar("demo_cliente", dict(reversed(list(seleccion.items()))),
                                  "web", catalogo)
    assert primero["registros_creados"] + segundo["registros_creados"] == 1
    assert segundo["duplicado"]
    assert primero["pedido"] == segundo["pedido"]
    assert seleccion == antes
    assert "demo_cliente" not in json.dumps(primero)
    skus = sorted(seleccion)
    texto = 'demo_cliente|' + json.dumps(skus, separators=(",", ":")) + '|'
    texto += json.dumps([seleccion[s] for s in skus], separators=(",", ":")) + '|web'
    assert primero["pedido"]["clave"] == hashlib.sha256(texto.encode()).hexdigest()
    segundo["pedido"]["seleccion"].clear()
    assert registro.registrar("demo_cliente", seleccion, "web", catalogo)["pedido"]["seleccion"]


def test_hash_cambia_con_cliente_cantidad_canal(catalogo):
    base = clave_pedido("demo_uno", {"CPU-AMD-5600": 1}, "web", catalogo)
    variantes = [clave_pedido("demo_dos", {"CPU-AMD-5600": 1}, "web", catalogo),
                 clave_pedido("demo_uno", {"CPU-AMD-5600": 2}, "web", catalogo),
                 clave_pedido("demo_uno", {"CPU-AMD-5600": 1}, "whatsapp", catalogo)]
    assert len({base, *variantes}) == 4
    with pytest.raises(ValueError):
        clave_pedido("persona@example.test", {"CPU-AMD-5600": 1}, "web", catalogo)


@pytest.mark.parametrize("maximo", [120000, 200000, 350000, 500000, 800000])
def test_cp7_rangos_sin_promesas_imposibles(catalogo, maximo):
    resultado = armar(catalogo, maximo_centimos=maximo)
    if resultado["cotizacion"] is None:
        assert resultado["minimo_catalogo_centimos"] > maximo
    else:
        cotizacion = resultado["cotizacion"]
        assert cotizacion["total_centimos"] <= maximo
        assert cotizacion["stock"]["disponible"]
        assert cotizacion["tecnico"]["sin_conflictos_datos"]
        assert cotizacion["hitl_requerido"] and not cotizacion["genera_proforma"]


def test_armador_abierto_mas_barato_y_minimo(catalogo):
    barato = armar(catalogo)
    assert barato["cotizacion"]["total_centimos"] == barato["minimo_catalogo_centimos"]
    abierto = armar(catalogo, minimo_centimos=500000)
    assert abierto["cotizacion"]["total_centimos"] >= 500000
    assert abierto["criterio"] == "menor_total"


def test_cp4_presupuesto_insuficiente_rtx(catalogo):
    resultado = armar(catalogo, maximo_centimos=120000, solo_rtx=True)
    assert resultado["cotizacion"] is None
    assert resultado["minimo_catalogo_centimos"] > 120000


def test_rango_invertido_y_booleano_rechazados(catalogo):
    with pytest.raises(ValueError):
        armar(catalogo, 500000, 100000)
    with pytest.raises(ValueError):
        armar(catalogo, maximo_centimos=True)


def test_no_stock_no_hay_minimo_inventado(catalogo):
    for producto in catalogo._productos.values():
        producto["stock"] = 0
    resultado = armar(catalogo)
    assert resultado["cotizacion"] is None
    assert resultado["minimo_catalogo_centimos"] is None


def test_buscador_contra_enumeracion_exhaustiva_pequena(catalogo, seleccion):
    from itertools import product

    extras = ["CPU-AMD-5600X", "MB-B550-DDR4", "GPU-RTX3050", "RAM-DDR4-16-3200",
              "SSD-NVME-1000-G3", "PSU-550", "CASE-02", "COOL-03"]
    permitidos = set(seleccion) | set(extras)
    catalogo._productos = {s: p for s, p in catalogo._productos.items() if s in permitidos}
    categorias = sorted({p["categoria"] for p in catalogo.listar()})
    opciones = [[p["sku"] for p in catalogo.listar(c) if p["stock"] > 0] for c in categorias]
    costos = []
    for skus in product(*opciones):
        propuesta = cotizar(catalogo, dict.fromkeys(skus, 1))
        if not propuesta["bloqueos"]:
            costos.append(propuesta["total_centimos"])
    assert costos
    menor, mayor = min(costos), max(costos)
    for minimo, maximo in [(0, menor - 1), (menor, menor), (menor + 1, mayor - 1),
                           (mayor, mayor), (mayor + 1, mayor + 2)]:
        candidatos = [c for c in costos if minimo <= c <= maximo]
        resultado = armar(catalogo, minimo, maximo)
        assert resultado["minimo_catalogo_centimos"] == menor
        if candidatos:
            assert resultado["cotizacion"]["total_centimos"] == max(candidatos)
        else:
            assert resultado["cotizacion"] is None
    for minimo in (0, menor + 1, mayor + 1):
        candidatos = [c for c in costos if c >= minimo]
        resultado = armar(catalogo, minimo)
        assert (resultado["cotizacion"]["total_centimos"] if candidatos
                else resultado["cotizacion"]) == (min(candidatos) if candidatos else None)


def test_presupuestos_mayores_producen_propuestas_distintas(catalogo):
    propuestas = [armar(catalogo, maximo_centimos=maximo)["cotizacion"]
                  for maximo in (350000, 500000, 800000)]
    selecciones = [tuple(linea["sku"] for linea in p["lineas"]) for p in propuestas]
    assert len(set(selecciones)) == 3

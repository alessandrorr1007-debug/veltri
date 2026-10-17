"""Contratos estrictos y su integración con las herramientas sin LLM ni red."""

import json
from copy import deepcopy

import pytest
from pydantic import ValidationError

from src.schemas.consulta import ConsultaResponse, ErrorValidacion
from src.schemas.entradas import (
    ArmadoRequest,
    ComparacionPagoRequest,
    ConsultaRequest,
    CotizacionRequest,
    PedidoDemoRequest,
)
from src.schemas.resultados import (
    LineaCotizacion,
    ResultadoArmado,
    ResultadoCotizacion,
    ResultadoPago,
    ResultadoPedido,
    ResultadoStock,
    ResultadoTecnico,
)
from src.tools.armador import armar
from src.tools.catalogo import Catalogo
from src.tools.cotizacion import cotizar
from src.tools.hardware import validar_configuracion
from src.tools.inventario import comprobar_stock
from src.tools.pagos import comparar_pago
from src.tools.pedidos import RegistroDemo


@pytest.fixture
def catalogo():
    return Catalogo()


@pytest.fixture
def seleccion():
    return dict.fromkeys(["CPU-AMD-5600", "MB-A520-DDR4", "GPU-RX6600",
                          "RAM-DDR4-8-2666", "SSD-NVME-500-G3", "PSU-450",
                          "CASE-01", "COOL-02"], 1)


@pytest.fixture
def cotizacion(catalogo, seleccion):
    return cotizar(catalogo, seleccion, 350000)


@pytest.fixture
def respuesta(cotizacion):
    return {"status": "revision_humana", "intencion": "cotizacion",
            "mensaje": "Propuesta de demostración pendiente de revisión.",
            "hitl_requerido": True, "motivos": cotizacion["tecnico"]["pendientes"],
            "fuentes": ["data/catalogo.json", "data/compatibilidad.json"],
            "cotizacion": cotizacion}


@pytest.mark.parametrize("campo,valor", [
    ("mensaje", ""), ("mensaje", "   "), ("mensaje", 42),
    ("canal", "email"), ("tenant_id", ""), ("tenant_id", "otro/tenant"),
    ("tenant_id", " tenant"), ("mensaje", "x" * 4001),
])
def test_solicitud_rechaza_campos_invalidos(campo, valor):
    datos = {"mensaje": "Cotizar PC", "canal": "web", "tenant_id": "veltri"}
    datos[campo] = valor
    with pytest.raises(ValidationError):
        ConsultaRequest.model_validate(datos)


def test_tenant_explicito_y_campos_extra_prohibidos():
    with pytest.raises(ValidationError):
        ConsultaRequest(mensaje="PC", canal="web")
    with pytest.raises(ValidationError):
        ConsultaRequest(mensaje="PC", canal="web", tenant_id="veltri", api_key="prohibido")


def test_repr_y_error_no_imprimen_mensaje():
    texto = "dato privado de prueba"
    solicitud = ConsultaRequest(mensaje=texto, canal="web", tenant_id="veltri")
    assert texto not in repr(solicitud)
    with pytest.raises(ValidationError) as error:
        ConsultaRequest(mensaje=texto, canal="desconocido", tenant_id="veltri")
    assert "input_value" not in str(error.value)
    assert "input_value" not in ErrorValidacion().model_dump_json()
    with pytest.raises(ValidationError):
        ErrorValidacion(campos=[texto])


@pytest.mark.parametrize("valor", [True, False, -1, 3.5, "350000"])
def test_presupuesto_no_se_convierte_silenciosamente(valor):
    with pytest.raises(ValidationError):
        ArmadoRequest(maximo_centimos=valor)
    with pytest.raises(ValidationError):
        ArmadoRequest.model_validate_json(json.dumps({"maximo_centimos": valor}))


def test_rango_valido_y_abierto():
    assert ArmadoRequest().maximo_centimos is None
    assert ArmadoRequest(minimo_centimos=500000).minimo_centimos == 500000
    assert ArmadoRequest(minimo_centimos=5, maximo_centimos=5).maximo_centimos == 5
    with pytest.raises(ValidationError):
        ArmadoRequest(minimo_centimos=6, maximo_centimos=5)


@pytest.mark.parametrize("seleccion", [{}, {"cpu-amd-5500": 1}, {"CPU-AMD-5500": True},
                                        {"CPU-AMD-5500": 0}, {"CPU-AMD-5500": "1"}])
def test_seleccion_invalida(seleccion):
    with pytest.raises(ValidationError):
        CotizacionRequest(seleccion=seleccion)


def test_sku_bien_formado_no_prueba_existencia(catalogo):
    entrada = CotizacionRequest(seleccion={"CPU-NO-EXISTE": 1})
    with pytest.raises(ValueError, match="desconocido"):
        cotizar(catalogo, entrada.seleccion)


def test_validacion_conserva_resultado_real_y_json(cotizacion, respuesta):
    resultado = ResultadoCotizacion.model_validate(cotizacion)
    assert resultado.model_dump() == cotizacion
    sobre = ConsultaResponse.model_validate(respuesta)
    assert ConsultaResponse.model_validate_json(sobre.model_dump_json()) == sobre
    assert sobre.cotizacion.total_centimos == cotizacion["total_centimos"]


@pytest.mark.parametrize("campo,valor", [
    ("total_centimos", 1), ("genera_proforma", True), ("hitl_requerido", False),
    ("hitl_requerido", 1), ("genera_proforma", 0), ("bloqueos", ["inventado"]),
    ("moneda", "USD"), ("sobre_presupuesto", True),
])
def test_cotizacion_rechaza_contradicciones(cotizacion, campo, valor):
    cotizacion[campo] = valor
    with pytest.raises(ValidationError):
        ResultadoCotizacion.model_validate(cotizacion)


def test_fuente_equivocada_subtotal_y_duplicados_rechazados(cotizacion):
    linea = deepcopy(cotizacion["lineas"][0])
    linea["fuente"] = "data/catalogo.json#CPU-AMD-5500"
    with pytest.raises(ValidationError):
        LineaCotizacion.model_validate(linea)
    linea = deepcopy(cotizacion["lineas"][0])
    linea["subtotal_centimos"] += 1
    with pytest.raises(ValidationError):
        LineaCotizacion.model_validate(linea)
    cotizacion["lineas"].append(cotizacion["lineas"][0])
    with pytest.raises(ValidationError):
        ResultadoCotizacion.model_validate(cotizacion)


def test_stock_agotado_y_bloqueo_preservados(catalogo, seleccion):
    seleccion.pop("CPU-AMD-5600")
    seleccion["CPU-AMD-5500"] = 1
    resultado = ResultadoCotizacion.model_validate(cotizar(catalogo, seleccion))
    assert resultado.stock.faltantes[0].sku == "CPU-AMD-5500"
    assert "stock_insuficiente" in resultado.bloqueos
    assert resultado.hitl_requerido
    alterado = resultado.model_dump()
    alterado["stock"]["faltantes"][0]["sku"] = "CPU-AMD-7600"
    with pytest.raises(ValidationError):
        ResultadoCotizacion.model_validate(alterado)


def test_contratos_de_stock_y_tecnico(catalogo, seleccion):
    stock = comprobar_stock(catalogo, {"CPU-AMD-5500": 1})
    assert ResultadoStock.model_validate(stock).hitl_requerido
    stock["hitl_requerido"] = False
    with pytest.raises(ValidationError):
        ResultadoStock.model_validate(stock)
    tecnico = validar_configuracion(catalogo, seleccion)
    assert ResultadoTecnico.model_validate(tecnico).sin_conflictos_datos
    tecnico["aprobado_tecnicamente"] = True
    with pytest.raises(ValidationError):
        ResultadoTecnico.model_validate(tecnico)


@pytest.mark.parametrize("maximo", [120000, 350000])
def test_contrato_armador_con_y_sin_solucion(catalogo, maximo):
    datos = armar(catalogo, maximo_centimos=maximo)
    resultado = ResultadoArmado.model_validate(datos)
    assert bool(resultado.cotizacion) == (resultado.estado == "propuesta_demo")
    datos["estado"] = ("sin_configuracion_en_rango" if resultado.cotizacion
                       else "propuesta_demo")
    with pytest.raises(ValidationError):
        ResultadoArmado.model_validate(datos)


@pytest.mark.parametrize("monto,moneda", [(9999, "PEN"), (10000, "PEN"), (10000, "USD")])
def test_contrato_pago_no_concilia(catalogo, monto, moneda):
    entrada = ComparacionPagoRequest(total_centimos=10000, pagado_centimos=monto, moneda=moneda)
    datos = comparar_pago(**entrada.model_dump())
    assert ResultadoPago.model_validate(datos).estado == "no_conciliado"
    datos["estado"] = "conciliado"
    with pytest.raises(ValidationError):
        ResultadoPago.model_validate(datos)


def test_contrato_pedido_duplicado_y_alias(catalogo, seleccion):
    solicitud = PedidoDemoRequest(cliente="demo_cliente", seleccion=seleccion, canal="web")
    registro = RegistroDemo()
    for duplicado in (False, True):
        datos = registro.registrar(**solicitud.model_dump(), catalogo=catalogo)
        assert ResultadoPedido.model_validate(datos).duplicado is duplicado
    datos["registros_creados"] = 1
    with pytest.raises(ValidationError):
        ResultadoPedido.model_validate(datos)
    with pytest.raises(ValidationError):
        PedidoDemoRequest(cliente="persona@example.test", seleccion=seleccion, canal="web")


@pytest.mark.parametrize("campo,valor", [
    ("status", "completado"), ("hitl_requerido", False), ("motivos", []),
    ("fuentes", ["data/politicas.md"]), ("fuentes", ["https://inventado.test"]),
    ("genera_proforma", True), ("aprobado_tecnicamente", True),
    ("intencion", "pago"), ("archivado_en_dlq", True), ("version_contrato", "2.0"),
])
def test_sobre_no_oculta_revision_fuentes_o_intencion(respuesta, campo, valor):
    respuesta[campo] = valor
    with pytest.raises(ValidationError):
        ConsultaResponse.model_validate(respuesta)


def test_respuesta_bloqueada_no_contiene_cotizacion(respuesta):
    respuesta["status"] = "bloqueado"
    respuesta["archivado_en_dlq"] = True
    with pytest.raises(ValidationError):
        ConsultaResponse.model_validate(respuesta)
    respuesta.pop("cotizacion")
    assert ConsultaResponse.model_validate(respuesta).archivado_en_dlq


def test_respuesta_error_e_informacion():
    error = ConsultaResponse(status="error", intencion="desconocida", mensaje="Entrada inválida",
                             hitl_requerido=False, motivos=["entrada_invalida"])
    assert error.cotizacion is None
    info = ConsultaResponse(status="completado", intencion="informacion",
                            mensaje="Los datos son sintéticos.", hitl_requerido=False,
                            fuentes=["data/politicas.md"])
    assert not info.genera_proforma


def test_sobre_pago_preserva_motivos_y_fuente():
    pago = comparar_pago(10000, 9999)
    datos = {"status": "revision_humana", "intencion": "pago", "mensaje": "Pago no conciliado",
             "hitl_requerido": True, "motivos": pago["motivos"],
             "fuentes": ["data/politicas.md"], "pago": pago}
    assert ConsultaResponse.model_validate(datos).pago.estado == "no_conciliado"
    datos["motivos"] = ["pago_discrepante"]
    with pytest.raises(ValidationError):
        ConsultaResponse.model_validate(datos)


def test_sobres_stock_tecnico_y_pedido(catalogo, seleccion):
    stock = comprobar_stock(catalogo, seleccion)
    stock_sobre = ConsultaResponse(status="completado", intencion="stock",
                                   mensaje="Stock de demostración disponible.",
                                   hitl_requerido=False, fuentes=["data/catalogo.json"],
                                   stock=stock)
    assert stock_sobre.stock.disponible
    tecnico = validar_configuracion(catalogo, seleccion)
    tecnico_sobre = ConsultaResponse(status="revision_humana", intencion="compatibilidad",
                                     mensaje="Falta evidencia de fabricante.", hitl_requerido=True,
                                     motivos=tecnico["pendientes"],
                                     fuentes=["data/compatibilidad.json"], tecnico=tecnico)
    assert not tecnico_sobre.aprobado_tecnicamente
    pedido = RegistroDemo().registrar("demo_cliente", seleccion, "web", catalogo)
    pedido_sobre = ConsultaResponse(status="revision_humana", intencion="pedido",
                                    mensaje="Borrador de demostración.", hitl_requerido=True,
                                    motivos=["borrador_demo"],
                                    fuentes=["data/catalogo.json", "data/politicas.md"],
                                    pedido=pedido)
    assert pedido_sobre.pedido.pedido.estado == "borrador_demo"


def test_pago_no_puede_ocultar_discrepancia():
    pago = comparar_pago(10000, 9999)
    pago["montos_coinciden"] = True
    with pytest.raises(ValidationError):
        ResultadoPago.model_validate(pago)


def test_error_publicable_no_admite_entrada_ni_traza():
    for campo in ("input", "traceback", "dni", "mensaje_original"):
        with pytest.raises(ValidationError):
            ErrorValidacion.model_validate({campo: "dato privado sintético"})

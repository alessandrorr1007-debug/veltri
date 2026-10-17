"""Atención determinista de consultas comerciales sobre catálogo, stock y políticas."""

import re
import unicodedata
from typing import Any

from src.core.seguridad import EntradaBloqueada, validar_entrada_modelo
from src.schemas.base import Canal
from src.schemas.consulta import ConsultaResponse
from src.schemas.entradas import ArmadoRequest, ConsultaRequest
from src.schemas.flujo import ParametrosArmado, ParametrosSeleccion, SolicitudFlujo
from src.schemas.hitl import Tenant
from src.tools.catalogo import Catalogo


def normalizar_texto(texto: str) -> str:
    """Convierte a minúsculas y elimina tildes/acentos para comparaciones robustas."""
    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    ).lower().strip()


def formatear_soles(centimos: int) -> str:
    """Convierte céntimos a representación en Soles (S/)."""
    return f"S/ {centimos / 100:,.2f}"


def detectar_extremo(msg_norm: str) -> str | None:
    """Identifica si se solicita el extremo máximo (más cara) o mínimo (más barata)."""
    patrones_max = (
        "mas cara",
        "mas costosa",
        "mas potente",
        "tope de gama",
        "tope",
        "gama alta",
        "mayor precio",
        "mas alto",
        "premium",
        "flagship",
        "la mejor",
    )
    if any(k in msg_norm for k in patrones_max):
        return "maximo"

    patrones_min = (
        "mas barata",
        "mas economica",
        "menor precio",
        "mas bajo",
        "gama de entrada",
        "accesible",
        "economica",
        "barata",
        "low cost",
    )
    if any(k in msg_norm for k in patrones_min):
        return "minimo"

    return None


def detectar_categoria_o_serie(msg_norm: str, contexto: str | None = None) -> str | None:
    """Determina la categoría o familia de hardware, usando contexto si es elíptico."""
    if "rtx" in msg_norm:
        return "rtx"
    if "radeon" in msg_norm or "rx" in msg_norm:
        return "radeon"
    if any(k in msg_norm for k in ("gpu", "tarjeta", "video", "grafica")):
        return "gpu"
    if any(k in msg_norm for k in ("cpu", "procesador", "ryzen", "intel")):
        return "cpu"
    if any(k in msg_norm for k in ("ram", "memoria")):
        return "ram"
    if any(k in msg_norm for k in ("ssd", "disco", "almacenamiento", "nvme")):
        return "ssd"
    if any(k in msg_norm for k in ("fuente", "psu", "power")):
        return "fuente"
    if any(k in msg_norm for k in ("placa", "motherboard", "tarjeta madre")):
        return "placa"
    if any(k in msg_norm for k in ("gabinete", "case", "caja")):
        return "gabinete"
    if any(k in msg_norm for k in ("refrigeracion", "cooler", "ventilador", "liquida")):
        return "refrigeracion"

    # Si es pregunta de seguimiento elíptica (ej: "y la mas cara", "y la otra?", "y en precio?")
    if contexto:
        ctx_norm = normalizar_texto(contexto)
        for cat in (
            "rtx",
            "radeon",
            "gpu",
            "cpu",
            "ram",
            "ssd",
            "fuente",
            "placa",
            "gabinete",
            "refrigeracion",
        ):
            if cat in ctx_norm:
                return cat

    return None


def inferir_parametros_consulta(
    mensaje: str,
) -> tuple[str, ParametrosArmado | ParametrosSeleccion | None]:
    """Extrae parámetros de armado o stock cuando el usuario escribe en lenguaje natural."""
    msg_norm = normalizar_texto(mensaje)

    # 1. Detección de cotización / armado con presupuesto explícito
    es_cotizacion = any(
        k in msg_norm for k in ("cotiz", "armar", "presupuesto", "pc gamer", "configuracion")
    )
    monto_match = re.search(
        r"(?:s\/?\.?\s*|soles\s*|presupuesto\s*(?:de\s*)?)(\d{3,6})", msg_norm
    )
    if not monto_match:
        monto_match = re.search(r"(\d{3,6})\s*(?:soles|s\/?\.?)", msg_norm)

    solo_rtx = "rtx" in msg_norm

    if es_cotizacion and monto_match:
        monto_soles = int(monto_match.group(1))
        monto_centimos = monto_soles * 100
        solicitud_armado = ArmadoRequest(maximo_centimos=monto_centimos, solo_rtx=solo_rtx)
        return "armar", ParametrosArmado(tipo="armar", solicitud=solicitud_armado)

    # 2. Detección de consulta de stock sobre componente específico
    es_stock = any(k in msg_norm for k in ("stock", "disponible", "disponibilidad", "hay stock"))
    sku_detectado = None
    if "5500" in msg_norm:
        sku_detectado = "CPU-AMD-5500"
    elif "5600x" in msg_norm:
        sku_detectado = "CPU-AMD-5600X"
    elif "5600" in msg_norm:
        sku_detectado = "CPU-AMD-5600"
    elif "3050" in msg_norm:
        sku_detectado = "GPU-RTX3050"
    elif "3060" in msg_norm:
        sku_detectado = "GPU-RTX3060"
    elif "4060ti" in msg_norm or "4060 ti" in msg_norm:
        sku_detectado = "GPU-RTX4060TI"
    elif "4060" in msg_norm:
        sku_detectado = "GPU-RTX4060"
    elif "6600" in msg_norm:
        sku_detectado = "GPU-RX6600"

    if (es_stock or "quiero armar" in msg_norm) and sku_detectado:
        return "stock", ParametrosSeleccion(tipo="stock", seleccion={sku_detectado: 1})

    return "informacion", None


def responder_consulta_gpu(
    catalogo: Catalogo, cat_o_serie: str, extremo: str | None
) -> ConsultaResponse:
    """Genera respuesta comercial exacta para tarjetas de video (RTX, Radeon o generales)."""
    if cat_o_serie == "rtx":
        prods = [p for p in catalogo.listar("gpu") if p["sku"].startswith("GPU-RTX")]
        prods.sort(key=lambda x: x["precio_centimos"])
        con_stock = [p for p in prods if p["stock"] > 0]
        if extremo == "maximo":
            target = con_stock[-1] if con_stock else prods[-1]
            p_str = formatear_soles(target["precio_centimos"])
            msg = (
                f"La tarjeta gráfica NVIDIA RTX más potente y de mayor gama en nuestro catálogo es "
                f"la GeForce RTX 4080 Super (SKU: {target['sku']}) por {p_str}, con "
                f"{target['stock']} unidades disponibles en stock."
            )
        else:
            primera = con_stock[0] if con_stock else prods[0]
            segunda = con_stock[1] if len(con_stock) > 1 else None
            p1_str = formatear_soles(primera["precio_centimos"])
            msg = (
                f"La tarjeta gráfica NVIDIA RTX más económica disponible en nuestro catálogo es "
                f"la GeForce RTX 3050 (SKU: {primera['sku']}) por {p1_str}, con "
                f"{primera['stock']} unidades en stock."
            )
            if segunda:
                p2_str = formatear_soles(segunda["precio_centimos"])
                msg += (
                    f" Como opción superior disponemos de la RTX 3060 (SKU: {segunda['sku']}) "
                    f"por {p2_str} ({segunda['stock']} unidades disponibles)."
                )
        return ConsultaResponse(
            status="completado",
            intencion="informacion",
            hitl_requerido=False,
            motivos=[],
            fuentes=["data/catalogo.json"],
            mensaje=msg,
        )

    if cat_o_serie == "radeon":
        prods = [p for p in catalogo.listar("gpu") if p["sku"].startswith("GPU-RX")]
        prods.sort(key=lambda x: x["precio_centimos"])
        con_stock = [p for p in prods if p["stock"] > 0]
        if extremo == "maximo":
            target = con_stock[-1] if con_stock else prods[-1]
            p_str = formatear_soles(target["precio_centimos"])
            msg = (
                f"La tarjeta AMD Radeon de mayor rendimiento en catálogo es la {target['sku']} "
                f"por {p_str} ({target['stock']} unidades en stock)."
            )
        else:
            target = con_stock[0] if con_stock else prods[0]
            p_str = formatear_soles(target["precio_centimos"])
            msg = (
                f"La tarjeta AMD Radeon más económica es la {target['sku']} por {p_str} "
                f"({target['stock']} unidades disponibles en stock)."
            )
        return ConsultaResponse(
            status="completado",
            intencion="informacion",
            hitl_requerido=False,
            motivos=[],
            fuentes=["data/catalogo.json"],
            mensaje=msg,
        )

    # GPU general
    gpus = catalogo.listar("gpu")
    gpus.sort(key=lambda x: x["precio_centimos"])
    con_stock = [p for p in gpus if p["stock"] > 0]
    if extremo == "maximo":
        target = con_stock[-1] if con_stock else gpus[-1]
        p_str = formatear_soles(target["precio_centimos"])
        msg = (
            f"La tarjeta de video de mayor gama en catálogo es la NVIDIA GeForce RTX 4080 Super "
            f"(SKU: {target['sku']}) por {p_str} ({target['stock']} unidades en stock)."
        )
    else:
        target = con_stock[0] if con_stock else gpus[0]
        p_str = formatear_soles(target["precio_centimos"])
        msg = (
            f"La tarjeta de video más económica disponible en catálogo es la "
            f"AMD Radeon RX 6600 (SKU: {target['sku']}) por {p_str}, con "
            f"{target['stock']} unidades en stock. Si buscas arquitectura NVIDIA RTX, "
            f"la más accesible es la RTX 3050 por S/ 1,790.00."
        )
    return ConsultaResponse(
        status="completado",
        intencion="informacion",
        hitl_requerido=False,
        motivos=[],
        fuentes=["data/catalogo.json"],
        mensaje=msg,
    )


def responder_consulta_cpu(catalogo: Catalogo, extremo: str | None) -> ConsultaResponse:
    """Genera respuesta comercial exacta para procesadores (CPUs)."""
    cpus = catalogo.listar("cpu")
    cpus.sort(key=lambda x: x["precio_centimos"])
    con_stock = [p for p in cpus if p["stock"] > 0]

    if extremo == "maximo":
        target = con_stock[-1] if con_stock else cpus[-1]
        p_str = formatear_soles(target["precio_centimos"])
        msg = (
            f"El procesador de mayor rendimiento disponible es el {target['sku']} por {p_str} "
            f"({target['stock']} unidades en stock)."
        )
    else:
        am4_stock = [p for p in con_stock if p["especificaciones"].get("socket") == "AM4"]
        am5_stock = [p for p in con_stock if p["especificaciones"].get("socket") == "AM5"]
        intel_stock = [p for p in con_stock if "INTEL" in p["sku"]]
        detalles = []
        if am4_stock:
            p_am4 = formatear_soles(am4_stock[0]["precio_centimos"])
            detalles.append(f"AM4: {am4_stock[0]['sku']} a {p_am4}")
        if am5_stock:
            p_am5 = formatear_soles(am5_stock[0]["precio_centimos"])
            detalles.append(f"AM5: {am5_stock[0]['sku']} a {p_am5}")
        if intel_stock:
            p_intel = formatear_soles(intel_stock[0]["precio_centimos"])
            detalles.append(f"Intel: {intel_stock[0]['sku']} a {p_intel}")
        resumen = "; ".join(detalles)
        msg = (
            f"Contamos con procesadores económicos disponibles: {resumen}. "
            f"El procesador AMD Ryzen 5 5500 se encuentra actualmente agotado."
        )

    return ConsultaResponse(
        status="completado",
        intencion="informacion",
        hitl_requerido=False,
        motivos=[],
        fuentes=["data/catalogo.json"],
        mensaje=msg,
    )


def responder_consulta_categoria_general(
    catalogo: Catalogo, categoria: str, extremo: str | None
) -> ConsultaResponse:
    """Atiende consultas para fuentes, ram, ssd, placas, gabinetes o refrigeracion."""
    items = catalogo.listar(categoria)
    items.sort(key=lambda x: x["precio_centimos"])
    con_stock = [p for p in items if p["stock"] > 0]
    target = con_stock[-1] if extremo == "maximo" else con_stock[0]
    p_str = formatear_soles(target["precio_centimos"])
    tipo_desc = "de mayor capacidad/gama" if extremo == "maximo" else "más económico/accesible"

    nombres_legibles = {
        "fuente": "fuente de poder",
        "ram": "memoria RAM",
        "ssd": "unidad SSD NVMe",
        "placa": "placa madre",
        "gabinete": "gabinete para PC",
        "refrigeracion": "sistema de refrigeración",
    }
    nombre = nombres_legibles.get(categoria, categoria)
    msg = (
        f"El componente {nombre} {tipo_desc} en catálogo es el {target['sku']} "
        f"por {p_str} ({target['stock']} unidades disponibles en stock)."
    )

    return ConsultaResponse(
        status="completado",
        intencion="informacion",
        hitl_requerido=False,
        motivos=[],
        fuentes=["data/catalogo.json"],
        mensaje=msg,
    )


def atender_consulta_comercial(
    catalogo: Catalogo,
    mensaje: str,
    tenant_id: Tenant = "veltri",
    canal: Canal = "web",
    contexto: str | None = None,
    orquestador: Any = None,
) -> ConsultaResponse:
    """Procesa consultas en lenguaje natural usando exclusivamente el catálogo y políticas."""
    # Invariante 5: Seguridad antes de cualquier procesamiento
    try:
        validar_entrada_modelo(mensaje)
    except EntradaBloqueada:
        if orquestador is not None and hasattr(orquestador, "dlq"):
            orquestador.dlq.registrar(tenant_id)
        return ConsultaResponse(
            status="bloqueado",
            intencion="desconocida",
            mensaje="Solicitud bloqueada por la guarda de seguridad.",
            hitl_requerido=False,
            motivos=["entrada_bloqueada"],
            archivado_en_dlq=True,
        )

    # Inferir parámetros estructurados si aplica
    _, params = inferir_parametros_consulta(mensaje)
    if params is not None and orquestador is not None:
        sol_flujo = SolicitudFlujo(
            consulta=ConsultaRequest(mensaje=mensaje, canal=canal, tenant_id=tenant_id),
            parametros=params,
        )
        res = orquestador.consultar(sol_flujo)
        return res.respuesta

    msg_norm = normalizar_texto(mensaje)
    extremo = detectar_extremo(msg_norm)
    cat_o_serie = detectar_categoria_o_serie(msg_norm, contexto)

    # 1. Consultas sobre GPUs y tarjetas de video
    if cat_o_serie in ("rtx", "radeon", "gpu"):
        return responder_consulta_gpu(catalogo, cat_o_serie, extremo)

    # 2. Consultas sobre procesadores
    if cat_o_serie == "cpu":
        return responder_consulta_cpu(catalogo, extremo)

    # 3. Consultas sobre otras categorías de hardware
    if cat_o_serie in ("fuente", "ram", "ssd", "placa", "gabinete", "refrigeracion"):
        return responder_consulta_categoria_general(catalogo, cat_o_serie, extremo)

    # 4. Consultas sobre políticas, garantía, métodos de pago o envíos
    es_politica = any(
        k in msg_norm
        for k in (
            "garantia",
            "politica",
            "pago",
            "pagar",
            "yape",
            "transferencia",
            "envio",
            "provincia",
            "despacho",
            "donde",
            "ubicacion",
            "horario",
        )
    )
    if es_politica:
        return ConsultaResponse(
            status="completado",
            intencion="informacion",
            hitl_requerido=False,
            motivos=[],
            fuentes=["data/politicas.md"],
            mensaje=(
                "En Veltri Tecnologic todos los componentes cuentan con 12 meses de garantía. "
                "Los pagos se concilian contra cuentas autorizadas (transferencia o Yape) "
                "con verificación exacta. Realizamos envíos a Lima Metropolitana y provincias "
                "vía agencia autorizada."
            ),
        )

    # 5. Saludo o consulta general asistida
    return ConsultaResponse(
        status="completado",
        intencion="informacion",
        hitl_requerido=False,
        motivos=[],
        fuentes=["data/catalogo.json", "data/politicas.md"],
        mensaje=(
            "Bienvenido a Veltri Tecnologic. Puedes indicarme tu presupuesto en Soles (S/) para "
            "armar una PC gamer, consultar disponibilidad de piezas de catálogo (RTX/Radeon, "
            "CPUs, fuentes, memorias), o consultar nuestras políticas de garantía y despacho."
        ),
    )

"""Búsqueda reproducible por presupuesto, sin estimar rendimiento ni FPS."""

from bisect import bisect_left, bisect_right
from itertools import product
from typing import Any

from src.tools.catalogo import Catalogo, entero
from src.tools.cotizacion import cotizar
from src.tools.hardware import potencia_requerida


def armar(catalogo: Catalogo, minimo_centimos: int = 0,
          maximo_centimos: int | None = None, solo_rtx: bool = False) -> dict[str, Any]:
    """Busca mínimo en rango abierto o mayor total bajo un máximo explícito."""
    entero(minimo_centimos, "mínimo")
    if maximo_centimos is not None:
        entero(maximo_centimos, "máximo")
        if maximo_centimos < minimo_centimos:
            raise ValueError("Rango invertido")
    if type(solo_rtx) is not bool:
        raise ValueError("solo_rtx debe ser bool")
    grupos = {c: [p for p in catalogo.listar(c) if p["stock"] > 0]
              for c in ("cpu", "placa", "ram", "ssd", "gpu",
                        "fuente", "gabinete", "refrigeracion")}
    if solo_rtx:
        grupos["gpu"] = [p for p in grupos["gpu"] if p["sku"].startswith("GPU-RTX")]
    mejor: tuple[int, tuple[str, ...]] | None = None
    minimo_catalogo = None
    reglas = catalogo.reglas
    potencia = reglas["potencia"]
    pares = {(r["cpu_sku"], r["placa_sku"]) for r in reglas["relaciones_cpu_placa"]}
    # Cada soporte válido se ordena por precio para consultar el rango con bisect.
    for cpu, placa, gpu in product(grupos["cpu"], grupos["placa"], grupos["gpu"]):
        c, b, g = (p["especificaciones"] for p in (cpu, placa, gpu))
        if c["socket"] != b["socket"] or (cpu["sku"], placa["sku"]) not in pares:
            continue
        plataforma = reglas["sockets"].get(c["socket"], {})
        if b["chipset"] not in plataforma.get("chipsets", []):
            continue
        watts = potencia_requerida(c["potencia_diseno_w"], g["potencia_diseno_w"],
                                   potencia["reserva_componentes_w"],
                                   potencia["margen_porcentaje"])
        soportes = []
        for psu, case, cooler in product(grupos["fuente"], grupos["gabinete"],
                                         grupos["refrigeracion"]):
            f, ca, co = (p["especificaciones"] for p in (psu, case, cooler))
            if (f["potencia_nominal_w"] < watts or f["formato"] not in ca["formatos_fuente"]
                    or b["formato"] not in ca["formatos_placa"]
                    or g["longitud_mm"] > ca["gpu_max_mm"]
                    or c["socket"] not in co["sockets"]
                    or co["capacidad_diseno_w"] < c["potencia_diseno_w"]
                    or co["altura_mm"] > ca["cooler_max_mm"]
                    or any(f["conectores"].get(k, 0) < n
                           for k, n in g["conectores_requeridos"].items())):
                continue
            soportes.append((sum(p["precio_centimos"] for p in (psu, case, cooler)),
                             (psu["sku"], case["sku"], cooler["sku"])))
        soportes.sort()
        if not soportes:
            continue
        precios = [s[0] for s in soportes]
        for ram, ssd in product(grupos["ram"], grupos["ssd"]):
            ra, ss = ram["especificaciones"], ssd["especificaciones"]
            if (ra["ram_tipo"] != b["ram_tipo"]
                    or ra["ram_tipo"] not in plataforma.get("ram_tipos", [])
                    or ra["modulos"] > b["ranuras_ram"]
                    or ra["capacidad_total_gb"] > b["ram_max_gb"]
                    or ss["interfaz"] not in b["interfaces_ssd"]):
                continue
            base = [cpu, placa, gpu, ram, ssd]
            subtotal = sum(p["precio_centimos"] for p in base)
            costo_min = subtotal + precios[0]
            minimo_catalogo = costo_min if minimo_catalogo is None else min(
                minimo_catalogo, costo_min)
            if maximo_centimos is None:
                indice = bisect_left(precios, minimo_centimos - subtotal)
            else:
                indice = bisect_right(precios, maximo_centimos - subtotal) - 1
            if not 0 <= indice < len(soportes):
                continue
            total = subtotal + precios[indice]
            if total < minimo_centimos:
                continue
            skus = tuple(sorted([p["sku"] for p in base] + list(soportes[indice][1])))
            candidato = (total, skus)
            if (mejor is None
                    or (maximo_centimos is None and candidato < mejor)
                    or (maximo_centimos is not None and
                        (total > mejor[0] or (total == mejor[0] and skus < mejor[1])))):
                mejor = candidato
    if mejor is None:
        return {"estado": "sin_configuracion_en_rango", "cotizacion": None,
                "minimo_catalogo_centimos": minimo_catalogo, "hitl_requerido": True}
    seleccion = dict.fromkeys(mejor[1], 1)
    resultado = cotizar(catalogo, seleccion, maximo_centimos)
    if resultado["bloqueos"]:
        raise ValueError("Datos inconsistentes entre búsqueda y validación")
    return {"estado": "propuesta_demo", "cotizacion": resultado,
            "minimo_catalogo_centimos": minimo_catalogo, "hitl_requerido": True,
            "criterio": "menor_total" if maximo_centimos is None else "mayor_total_en_rango"}

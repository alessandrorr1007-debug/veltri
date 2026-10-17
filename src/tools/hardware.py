"""Cálculos de compatibilidad sobre fichas sintéticas; no certifica hardware real."""

from typing import Any

from src.tools.catalogo import Catalogo, entero

CATEGORIAS = ("cpu", "placa", "gpu", "ram", "ssd", "fuente", "gabinete", "refrigeracion")


def potencia_requerida(cpu_w: int, gpu_w: int, reserva_w: int, margen: int) -> int:
    """Redondea hacia arriba usando enteros; resultado estimado, no medido."""
    for valor in (cpu_w, gpu_w, reserva_w, margen):
        entero(valor, "potencia o margen")
    return ((cpu_w + gpu_w + reserva_w) * (100 + margen) + 99) // 100


def validar_configuracion(catalogo: Catalogo, seleccion: dict[str, int]) -> dict[str, Any]:
    """Valida una PC de una unidad por categoría, incluida GPU dedicada."""
    catalogo.lineas(seleccion)
    grupos: dict[str, list[dict[str, Any]]] = {c: [] for c in CATEGORIAS}
    conflictos = []
    for sku, cantidad in seleccion.items():
        p = catalogo.obtener(sku)
        if p["categoria"] not in grupos or cantidad != 1:
            conflictos.append("cantidad_o_categoria_no_admitida:" + sku)
        else:
            grupos[p["categoria"]].append(p)
    for categoria, productos in grupos.items():
        if len(productos) != 1:
            conflictos.append("requiere_un_componente:" + categoria)
    fuente = "data/compatibilidad.json"
    if conflictos:
        return {"sin_conflictos_datos": False, "aprobado_tecnicamente": False,
                "hitl_requerido": True, "conflictos": conflictos,
                "pendientes": [], "potencia_estimada_w": None, "fuente": fuente}
    datos = {c: ps[0]["especificaciones"] for c, ps in grupos.items()}
    cpu, placa, gpu, ram, ssd, psu, case, cooler = (datos[c] for c in CATEGORIAS)
    reglas = catalogo.reglas
    potencia = reglas["potencia"]
    watts = potencia_requerida(cpu["potencia_diseno_w"], gpu["potencia_diseno_w"],
                               potencia["reserva_componentes_w"], potencia["margen_porcentaje"])
    plataforma = reglas["sockets"].get(cpu["socket"], {})
    condiciones = {
        "socket_incompatible": cpu["socket"] == placa["socket"],
        "chipset_incompatible": placa["chipset"] in plataforma.get("chipsets", []),
        "ram_incompatible": ram["ram_tipo"] == placa["ram_tipo"]
                            and ram["ram_tipo"] in plataforma.get("ram_tipos", []),
        "ram_excede_ranuras": ram["modulos"] <= placa["ranuras_ram"],
        "ram_excede_capacidad": ram["capacidad_total_gb"] <= placa["ram_max_gb"],
        "ssd_incompatible": ssd["interfaz"] in placa["interfaces_ssd"],
        "cooler_socket_incompatible": cpu["socket"] in cooler["sockets"],
        "cooler_insuficiente": cooler["capacidad_diseno_w"] >= cpu["potencia_diseno_w"],
        "cooler_no_cabe": cooler["altura_mm"] <= case["cooler_max_mm"],
        "gpu_no_cabe": gpu["longitud_mm"] <= case["gpu_max_mm"],
        "placa_no_cabe": placa["formato"] in case["formatos_placa"],
        "fuente_no_cabe": psu["formato"] in case["formatos_fuente"],
        "fuente_insuficiente": psu["potencia_nominal_w"] >= watts,
        "conectores_insuficientes": all(psu["conectores"].get(k, 0) >= n
                                        for k, n in gpu["conectores_requeridos"].items()),
    }
    conflictos = [motivo for motivo, cumple in condiciones.items() if not cumple]
    pares = [p for p in reglas["relaciones_cpu_placa"]
             if p["cpu_sku"] == grupos["cpu"][0]["sku"]
             and p["placa_sku"] == grupos["placa"][0]["sku"]]
    pendientes = ["fichas_sinteticas", "validar_potencia_y_conectores_fabricante"]
    if not pares or any(p["estado"] != "verificado" for p in pares):
        pendientes.append("verificar_soporte_cpu_bios")
    return {"sin_conflictos_datos": not conflictos, "aprobado_tecnicamente": False,
            "hitl_requerido": True, "conflictos": conflictos, "pendientes": pendientes,
            "potencia_estimada_w": watts, "fuente": fuente}

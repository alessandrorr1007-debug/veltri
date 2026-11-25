"""Evaluación económica incremental de Veltri en PEN, independiente de la aplicación."""

import argparse
import json
import re
from dataclasses import asdict, dataclass, fields, replace
from decimal import ROUND_CEILING, Decimal, localcontext
from pathlib import Path

MESES = 36
MESES_ANIO = 12
CERO = Decimal(0)
UNO = Decimal(1)
RAIZ = Path(__file__).resolve().parents[1]
PERFIL = RAIZ / "evals/economia_semana13.json"
PROPORCIONES = {"proporcion_hitl", "reproceso_asis", "reproceso_tobe", "realizacion"}


def _decimal(valor, campo: str, maximo: Decimal | None = None) -> Decimal:
    """Acepta enteros y decimales exactos. Los importes JSON usan cadenas."""
    if type(valor) is int or isinstance(valor, Decimal):
        numero = Decimal(valor)
    elif isinstance(valor, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", valor):
        numero = Decimal(valor)
    else:
        raise ValueError(f"{campo}: usa un entero o decimal exacto")
    if not numero.is_finite() or numero < 0 or (maximo is not None and numero > maximo):
        raise ValueError(f"{campo}: valor fuera del rango admitido")
    return numero


@dataclass(frozen=True)
class Supuestos:
    """Volumen estable. Tiempos humanos activos por consulta y costo laboral por hora."""

    consultas_mes: int
    minutos_asis: Decimal
    minutos_tobe: Decimal
    minutos_revision: Decimal
    proporcion_hitl: Decimal
    reproceso_asis: Decimal
    reproceso_tobe: Decimal
    minutos_reproceso: Decimal
    costo_hora_pen: Decimal
    realizacion: Decimal

    def __post_init__(self):
        if type(self.consultas_mes) is not int or self.consultas_mes < 0:
            raise ValueError("consultas_mes: se requiere un entero no negativo")
        for campo in fields(self):
            nombre = campo.name
            if nombre != "consultas_mes":
                limite = UNO if nombre in PROPORCIONES else None
                object.__setattr__(self, nombre, _decimal(getattr(self, nombre), nombre, limite))

    def tiempos_por_consulta(self) -> dict:
        """La supervisión y el reproceso son subconjuntos distintos de trabajo activo."""
        return {
            "asis_rutina": self.minutos_asis,
            "asis_reproceso": self.reproceso_asis * self.minutos_reproceso,
            "tobe_rutina": self.minutos_tobe,
            "tobe_revision": self.proporcion_hitl * self.minutos_revision,
            "tobe_reproceso": self.reproceso_tobe * self.minutos_reproceso,
        }


@dataclass(frozen=True)
class Costo:
    """Partida única. La cantidad se aplica una vez al inicio o en cada mes."""

    id: str
    concepto: str
    clase: str
    alcance: str
    periodo: str
    cantidad: Decimal
    unidad: str
    unitario_pen: Decimal
    origen: str
    justificacion: str

    def __post_init__(self):
        opciones = {
            "clase": {"directo", "indirecto", "oculto", "oportunidad"},
            "alcance": {"compartido", "asis", "tobe"},
            "periodo": {"inicial", "mensual"},
            "origen": {"acreditado", "estimado", "supuesto"},
            "unidad": {"horas", "unidades", "kwh", "asignacion"},
        }
        for nombre, validos in opciones.items():
            valor = getattr(self, nombre)
            if not isinstance(valor, str) or valor not in validos:
                raise ValueError(f"Costo: {nombre} inválido")
        for nombre in ("id", "concepto", "justificacion"):
            if not isinstance(getattr(self, nombre), str) or not getattr(self, nombre).strip():
                raise ValueError(f"Costo: {nombre} obligatorio")
        for nombre in ("cantidad", "unitario_pen"):
            object.__setattr__(self, nombre, _decimal(getattr(self, nombre), nombre))

    def importe(self) -> Decimal:
        return self.cantidad * self.unitario_pen


def roi(beneficio: Decimal, costo: Decimal) -> Decimal | None:
    """Aplica la fórmula a un denominador positivo."""
    return (beneficio - costo) / costo * 100 if costo > 0 else None


def van(flujos: list[Decimal], tasa_anual: Decimal) -> Decimal:
    """El flujo 0 es inmediato. Los siguientes se sitúan al cierre de cada año."""
    tasa = _decimal(tasa_anual, "tasa_descuento_anual", UNO)
    return sum((flujo / (UNO + tasa) ** anio for anio, flujo in enumerate(flujos)), CERO)


def payback(inversion: Decimal, flujos_mensuales: list[Decimal]) -> dict:
    """Interpola dentro del primer mes en el que el acumulado llega a cero."""
    if inversion <= 0:
        return {"estado": "sin_inversion_incremental", "meses": None}
    acumulado = -inversion
    for mes, flujo in enumerate(flujos_mensuales, start=1):
        if acumulado + flujo >= 0:
            return {"estado": "recuperado", "meses": Decimal(mes - 1) - acumulado / flujo}
        acumulado += flujo
    return {"estado": "sin_recuperacion_en_horizonte", "meses": None}


def punto_equilibrio(objetivo_mensual: Decimal, beneficio_unitario: Decimal) -> int | None:
    """Umbral mínimo con margen creciente. None señala ausencia de umbral creciente."""
    if beneficio_unitario <= 0:
        return None
    cociente = max(CERO, objetivo_mensual) / beneficio_unitario
    return int(cociente.to_integral_value(rounding=ROUND_CEILING))


def _tco(inicial: Decimal, soporte: Decimal, mano_obra: Decimal) -> dict:
    mensual = soporte + mano_obra
    return {
        "inicial_pen": inicial, "soporte_mensual_pen": soporte, "labor_mensual_pen": mano_obra,
        "operacion_mensual_pen": mensual, "operacion_anual_pen": mensual * MESES_ANIO,
        "acumulado_por_anio_pen": [inicial + mensual * MESES_ANIO * a for a in range(1, 4)],
        "total_36_pen": inicial + mensual * MESES,
    }


def calcular(
    supuestos: Supuestos, costos: list[Costo], tasa_anual: Decimal, *,
    factor_inicial=UNO, factor_operacion=UNO,
) -> dict:
    """Compara TCO económicos y, por separado, el flujo incremental realizable."""
    tasa = _decimal(tasa_anual, "tasa_descuento_anual", UNO)
    factores = {
        "inicial": _decimal(factor_inicial, "factor_inicial"),
        "mensual": _decimal(factor_operacion, "factor_operacion"),
    }
    if len({costo.id for costo in costos}) != len(costos):
        raise ValueError("Los identificadores de costo deben ser únicos")
    with localcontext() as contexto:
        contexto.prec = 40
        return _calcular(supuestos, costos, tasa, factores)


def _calcular(s: Supuestos, costos: list[Costo], tasa: Decimal, factores: dict) -> dict:
    totales = {(alcance, periodo): CERO for alcance in ("asis", "tobe")
               for periodo in ("inicial", "mensual")}
    partidas = []
    for costo in costos:
        factor = factores[costo.periodo] if costo.alcance == "tobe" else UNO
        importe = costo.importe() * factor
        partidas.append({**asdict(costo), "importe_escenario_pen": importe})
        alcances = ("asis", "tobe") if costo.alcance == "compartido" else (costo.alcance,)
        for alcance in alcances:
            totales[alcance, costo.periodo] += importe

    tiempos = s.tiempos_por_consulta()
    asis = tiempos["asis_rutina"] + tiempos["asis_reproceso"]
    tobe = tiempos["tobe_rutina"] + tiempos["tobe_revision"] + tiempos["tobe_reproceso"]
    horas_liberadas = (asis - tobe) * s.consultas_mes / 60
    unitario = (asis - tobe) * s.costo_hora_pen * s.realizacion / 60
    bruto = horas_liberadas * s.costo_hora_pen
    realizable = unitario * s.consultas_mes
    tco = {}
    for alcance, minutos in (("asis", asis), ("tobe", tobe)):
        labor = minutos * s.consultas_mes * s.costo_hora_pen / 60
        tco[alcance] = _tco(totales[alcance, "inicial"], totales[alcance, "mensual"], labor)

    inversion = totales["tobe", "inicial"] - totales["asis", "inicial"]
    operacion = totales["tobe", "mensual"] - totales["asis", "mensual"]
    neto = realizable - operacion
    flujo_anual = [-inversion, *([neto * MESES_ANIO] * 3)]
    anualidad = sum((UNO / (UNO + tasa) ** anio for anio in range(1, 4)), CERO)
    return {
        "supuestos": asdict(s), "partidas": partidas, "tco": tco,
        "tiempos_por_consulta_min": {**tiempos, "asis_total": asis, "tobe_total": tobe},
        "horas_liberadas_mes": horas_liberadas,
        "capacidad_adicional_consultas_mes": (
            int(horas_liberadas * 60 / tobe) if tobe > 0 and horas_liberadas > 0 else 0
        ),
        "inversion_incremental_pen": inversion, "operacion_incremental_mes_pen": operacion,
        "bruto_economico_mes_pen": bruto, "bruto_economico_anio_pen": bruto * MESES_ANIO,
        "bruto_economico_36_pen": bruto * MESES, "realizable_mes_pen": realizable,
        "realizable_anio_pen": realizable * MESES_ANIO, "realizable_36_pen": realizable * MESES,
        "neto_mes_pen": neto, "neto_anio_estable_pen": neto * MESES_ANIO,
        "neto_anio_1_incluida_inversion_pen": neto * MESES_ANIO - inversion,
        "neto_36_pen": neto * MESES - inversion,
        "roi_anio_1_pct": roi(realizable * MESES_ANIO, inversion + operacion * MESES_ANIO),
        "roi_estable_anual_pct": roi(realizable * MESES_ANIO, operacion * MESES_ANIO),
        "roi_36_pct": roi(realizable * MESES, inversion + operacion * MESES),
        "flujo_anual_pen": flujo_anual,
        "flujo_acumulado_mensual_pen": [-inversion + neto * mes for mes in range(MESES + 1)],
        "payback": payback(inversion, [neto] * MESES),
        "van_pen": van(flujo_anual, tasa),
        "equilibrio_operativo_consultas_mes": punto_equilibrio(operacion, unitario),
        "equilibrio_36_consultas_mes": punto_equilibrio(operacion + inversion / MESES, unitario),
        "equilibrio_van_consultas_mes": punto_equilibrio(
            operacion + inversion / (MESES_ANIO * anualidad), unitario,
        ),
    }


def sensibilidad(s: Supuestos, costos: list[Costo], tasa: Decimal) -> list[dict]:
    """Prueba dos valores por variable frente a la misma base empresarial."""
    resultados = []
    ahorro_rutina = s.minutos_asis - s.minutos_tobe
    for factor, delta_tasa, delta_hitl in (
        (Decimal("0.8"), Decimal("-0.04"), Decimal("-0.10")),
        (Decimal("1.2"), Decimal("0.04"), Decimal("0.10")),
    ):
        volumen = int(Decimal(s.consultas_mes) * factor)
        minutos_tobe = max(CERO, s.minutos_asis - ahorro_rutina * factor)
        tasa_nueva = min(UNO, max(CERO, tasa + delta_tasa))
        hitl = min(UNO, max(CERO, s.proporcion_hitl + delta_hitl))
        casos = (
            ("consultas_mes", volumen, replace(s, consultas_mes=volumen), tasa, {}),
            ("minutos_ahorrados_rutina", s.minutos_asis - minutos_tobe,
             replace(s, minutos_tobe=minutos_tobe), tasa, {}),
            ("costo_hora_pen", s.costo_hora_pen * factor,
             replace(s, costo_hora_pen=s.costo_hora_pen * factor), tasa, {}),
            ("factor_operacion", factor, s, tasa, {"factor_operacion": factor}),
            ("factor_inicial", factor, s, tasa, {"factor_inicial": factor}),
            ("tasa_descuento_anual", tasa_nueva, s, tasa_nueva, {}),
            ("proporcion_hitl", hitl, replace(s, proporcion_hitl=hitl), tasa, {}),
        )
        for variable, valor, escenario, descuento, opciones in casos:
            salida = calcular(escenario, costos, descuento, **opciones)
            resultados.append({
                "variable": variable, "valor": valor, "van_pen": salida["van_pen"],
                "neto_mes_pen": salida["neto_mes_pen"], "roi_36_pct": salida["roi_36_pct"],
                "payback": salida["payback"],
            })
    return resultados


def _validar_campos(datos: dict, esperados: set[str], etiqueta: str) -> None:
    if not isinstance(datos, dict) or datos.keys() != esperados:
        raise ValueError(f"{etiqueta}: campos incompletos o desconocidos")


def generar_informe(perfil: dict) -> dict:
    """Aplica un perfil académico independiente y tres hipótesis empresariales."""
    _validar_campos(
        perfil, {"moneda", "tasa_descuento_anual", "academico", "empresarial"}, "perfil",
    )
    if perfil["moneda"] != "PEN":
        raise ValueError("El perfil solo admite PEN (soles peruanos)")
    tasa = _decimal(perfil["tasa_descuento_anual"], "tasa_descuento_anual", UNO)
    acad, empresa = perfil["academico"], perfil["empresarial"]
    _validar_campos(acad, {"supuestos", "costos"}, "academico")
    _validar_campos(empresa, {"supuestos", "costos", "variantes"}, "empresarial")
    _validar_campos(empresa["variantes"], {"pesimista", "optimista"}, "variantes")
    base = Supuestos(**empresa["supuestos"])
    costos = [Costo(**partida) for partida in empresa["costos"]]
    proyecciones = {"base": calcular(base, costos, tasa)}
    for nombre in ("pesimista", "optimista"):
        variante = empresa["variantes"][nombre]
        _validar_campos(variante, {"cambios", "factor_inicial", "factor_operacion"}, nombre)
        proyecciones[nombre] = calcular(
            replace(base, **variante["cambios"]), costos, tasa,
            factor_inicial=variante["factor_inicial"],
            factor_operacion=variante["factor_operacion"],
        )
    academico = calcular(
        Supuestos(**acad["supuestos"]), [Costo(**p) for p in acad["costos"]], tasa,
    )
    return {
        "moneda": "PEN", "meses": MESES, "tasa_descuento_anual": tasa,
        "supuestos_pendientes_revision": True,
        "academico": {"naturaleza": "estimacion_de_recursos_imputados", **academico},
        "empresarial": {
            nombre: {"naturaleza": "proyeccion_hipotetica", **salida}
            for nombre, salida in proyecciones.items()
        },
        "sensibilidad_empresarial": sensibilidad(base, costos, tasa),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--supuestos", type=Path, default=PERFIL)
    args = parser.parse_args()
    try:
        informe = generar_informe(json.loads(args.supuestos.read_text(encoding="utf-8")))
    except (OSError, TypeError, KeyError, ValueError) as error:
        parser.error(f"Perfil económico inválido: {error}")
    print(json.dumps(informe, default=str, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

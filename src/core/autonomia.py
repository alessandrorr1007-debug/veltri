"""Presupuesto compartido por consulta, con reservas y motivos de parada cerrados."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from threading import RLock
from time import monotonic
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

NaturalezaTokens = Literal["reales", "estimados", "simulados"]

MotivoParada = Literal[
    "limite_iteraciones", "limite_modelo", "limite_herramientas", "limite_tokens",
    "limite_tiempo", "limite_delegacion", "delegacion_circular", "delegacion_repetida",
    "herramienta_no_autorizada", "argumentos_no_autorizados", "presupuesto_anidado",
    "evidencia_invalida",
]


class LimitesAutonomia(BaseModel):
    """Valores de la demo académica; la fachada comercial usa su propio perfil."""

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    iteraciones: int = Field(default=32, ge=1, le=128)
    modelos: int = Field(default=14, ge=0, le=64)
    herramientas: int = Field(default=12, ge=0, le=128)
    profundidad: int = Field(default=1, ge=0, le=1)
    segundos: float = Field(default=10, gt=0, le=60, allow_inf_nan=False)
    tokens: int = Field(default=32_000, ge=1, le=256_000)
    salida_tokens: int = Field(default=128, ge=1, le=4096)


LIMITES_COMERCIALES = LimitesAutonomia(
    iteraciones=4, modelos=2, herramientas=91, profundidad=0, tokens=8192,
)


class EjecucionInterrumpida(RuntimeError):
    def __init__(self, motivo: MotivoParada):
        self.motivo = motivo
        super().__init__(motivo)


def estimar_tokens(texto: str) -> int:
    """Aproximación local de cuatro bytes UTF-8 por token, sin llamada al proveedor."""
    return (len(texto.encode()) + 3) // 4


class Presupuesto:
    """La instancia es compartida incluso entre trabajadores del mismo grafo."""

    def __init__(self, limites: LimitesAutonomia, reloj: Callable[[], float] = monotonic):
        self.limites = LimitesAutonomia.model_validate(limites.model_dump())
        self._reloj = reloj
        self._inicio = reloj()
        self._lock = RLock()
        self.motivo: MotivoParada | None = None
        self.iteraciones = self.modelos = self.herramientas = self.profundidad = 0
        self._delegaciones: set[str] = set()
        self._reservados = self._consumidos = 0
        self._tokens = {modo: {"entrada": 0, "salida": 0} for modo in (
            "reales", "estimados", "simulados",
        )}

    def registrar_parada(self, motivo: MotivoParada) -> MotivoParada:
        with self._lock:
            if self.motivo is None:
                self.motivo = motivo
            return self.motivo

    def detener(self, motivo: MotivoParada):
        raise EjecucionInterrumpida(self.registrar_parada(motivo))

    def segundos_restantes(self) -> float:
        with self._lock:
            if self.motivo is not None:
                raise EjecucionInterrumpida(self.motivo)
            restantes = self.limites.segundos - (self._reloj() - self._inicio)
            if restantes <= 0:
                self.detener("limite_tiempo")
            return restantes

    def paso(self) -> None:
        with self._lock:
            self.segundos_restantes()
            if self.iteraciones >= self.limites.iteraciones:
                self.detener("limite_iteraciones")
            self.iteraciones += 1

    def herramienta(self, *, delegacion: tuple[tuple[str, ...], str] | None = None) -> None:
        with self._lock:
            self.segundos_restantes()
            if self.herramientas >= self.limites.herramientas:
                self.detener("limite_herramientas")
            if delegacion is not None:
                self._delegar(*delegacion)
            self.herramientas += 1

    def _delegar(self, ruta: tuple[str, ...], destino: str) -> None:
        if destino in ruta:
            self.detener("delegacion_circular")
        if len(ruta) > self.limites.profundidad:
            self.detener("limite_delegacion")
        if destino in self._delegaciones:
            self.detener("delegacion_repetida")
        self._delegaciones.add(destino)
        self.profundidad = max(self.profundidad, len(ruta))

    def reservar_modelo(self, entrada: int) -> int:
        with self._lock:
            self.segundos_restantes()
            if self.modelos >= self.limites.modelos:
                self.detener("limite_modelo")
            salida = min(
                self.limites.salida_tokens,
                self.limites.tokens - self._consumidos - self._reservados - entrada,
            )
            if salida < 1:
                self.detener("limite_tokens")
            self._reservados += entrada + salida
            self.modelos += 1
            return salida

    def liquidar_modelo(
        self, entrada: int, reserva_salida: int, entrada_usada: int, salida_usada: int,
        naturaleza: NaturalezaTokens, *, naturaleza_salida: NaturalezaTokens | None = None,
        otros: int = 0,
    ) -> None:
        with self._lock:
            self._reservados -= entrada + reserva_salida
            self._tokens[naturaleza]["entrada"] += entrada_usada
            self._tokens[naturaleza_salida or naturaleza]["salida"] += salida_usada
            self._consumidos += entrada_usada + salida_usada + otros
            if salida_usada > reserva_salida or (
                self._consumidos + self._reservados > self.limites.tokens
            ):
                self.detener("limite_tokens")
            self.segundos_restantes()

    def metricas(self, *, hitl: bool, finalizacion: str = "completada") -> dict:
        with self._lock:
            return {
                "iteraciones": self.iteraciones, "modelos": self.modelos,
                "herramientas": self.herramientas, "delegaciones": len(self._delegaciones),
                "profundidad": self.profundidad, "tokens": {
                    modo: valores.copy() for modo, valores in self._tokens.items()
                },
                "tokens_cargados": self._consumidos,
                "tiempo_ms": round((self._reloj() - self._inicio) * 1000, 3),
                "finalizacion": self.motivo or finalizacion, "revisiones_humanas": int(hitl),
            }


presupuesto_actual: ContextVar[Presupuesto | None] = ContextVar(
    "presupuesto_autonomia", default=None,
)


@contextmanager
def controlar_ejecucion(
    limites: LimitesAutonomia, reloj: Callable[[], float] = monotonic,
) -> Iterator[Presupuesto]:
    existente = presupuesto_actual.get()
    if existente is not None:
        existente.detener("presupuesto_anidado")
    presupuesto = Presupuesto(limites, reloj)
    token = presupuesto_actual.set(presupuesto)
    try:
        yield presupuesto
    finally:
        presupuesto_actual.reset(token)

"""Cola local de bloqueos sin mensajes, huellas de texto ni datos personales."""

import hashlib
from threading import RLock
from uuid import uuid4

from src.schemas.base import Contrato, HashPedido
from src.schemas.hitl import Tenant


class EventoBloqueado(Contrato):
    """Solo identificador técnico y causa fija del bloqueo."""

    id: HashPedido
    tenant_id: Tenant
    codigo: str = "entrada_bloqueada"


class ColaBloqueos:
    """DLQ de demo en memoria; no persiste entre reinicios ni guarda consultas."""

    def __init__(self) -> None:
        self._eventos: list[EventoBloqueado] = []
        self._lock = RLock()

    def registrar(self, tenant: str) -> EventoBloqueado:
        """ID aleatorio independiente del mensaje; no permite reconstruirlo."""
        evento = EventoBloqueado(id=hashlib.sha256(uuid4().bytes).hexdigest(), tenant_id=tenant)
        with self._lock:
            self._eventos.append(evento)
        return EventoBloqueado.model_validate(evento.model_dump())

    def listar(self, tenant: str) -> list[EventoBloqueado]:
        """Filtra por tenant validado; sin mensajes o metadatos libres."""
        from pydantic import TypeAdapter

        tenant = TypeAdapter(Tenant).validate_python(tenant, strict=True)
        with self._lock:
            return [
                EventoBloqueado.model_validate(e.model_dump())
                for e in self._eventos
                if e.tenant_id == tenant
            ]

"""Bandeja local aislada por tenant; ninguna resolución ejecuta negocio."""

import hashlib
from threading import RLock

from src.core.decision import decide
from src.schemas.base import Contrato, HashPedido
from src.schemas.decision import SolicitudDecision
from src.schemas.hitl import ResolucionRevision, ResultadoEncolado, Revision
from src.schemas.hitl import Tenant as TipoTenant


class _Acceso(Contrato):
    """Valida claves sin reutilizar un tenant global o aceptar rutas de archivos."""

    tenant_id: TipoTenant
    id: HashPedido | None = None


class BandejaRevision:
    """Almacenamiento en memoria y bloqueo por instancia; no persiste ni autentica."""

    def __init__(self) -> None:
        self._registros: dict[tuple[str, str], Revision] = {}
        self._lock = RLock()

    def encolar(self, tenant: str, solicitud: SolicitudDecision) -> ResultadoEncolado:
        """Recalcula la decisión; no acepta un dict de decisión preautorizada."""
        acceso = _Acceso(tenant_id=tenant)
        solicitud = SolicitudDecision.model_validate(solicitud.model_dump())
        decision = decide(solicitud)
        if not decision.hitl_requerido:
            raise ValueError("La solicitud no requiere revisión")
        contenido_id = acceso.tenant_id + "|" + decision.hash_evidencia
        id_ = hashlib.sha256(contenido_id.encode()).hexdigest()
        clave = (acceso.tenant_id, id_)
        with self._lock:
            duplicado = clave in self._registros
            if not duplicado:
                self._registros[clave] = Revision(
                    id=id_, tenant_id=acceso.tenant_id, solicitud=solicitud, decision=decision,
                    estado="escalada" if decision.destino == "escalar" else "pendiente")
            return ResultadoEncolado(duplicado=duplicado,
                                      revision=Revision.model_validate(self._registros[clave].model_dump()))

    def obtener(self, tenant: str, id_: str) -> Revision:
        """Devuelve copia aislada; una clave ajena se comporta como inexistente."""
        acceso = _Acceso(tenant_id=tenant, id=id_)
        with self._lock:
            registro = self._registros.get((acceso.tenant_id, id_))
            if registro is None:
                raise ValueError("Revisión no encontrada")
            return Revision.model_validate(registro.model_dump())

    def listar(self, tenant: str) -> list[Revision]:
        """Lista solo revisiones del tenant explícito, en orden estable."""
        acceso = _Acceso(tenant_id=tenant)
        with self._lock:
            return [Revision.model_validate(r.model_dump()) for (t, _), r in
                    sorted(self._registros.items()) if t == acceso.tenant_id]

    def resolver(self, tenant: str, id_: str, resolucion: ResolucionRevision) -> Revision:
        """Impide aprobaciones con bloqueos y conserva resolución final idempotente."""
        resolucion = ResolucionRevision.model_validate(resolucion.model_dump())
        with self._lock:
            registro = self.obtener(tenant, id_)
            if registro.resolucion is not None:
                if registro.resolucion == resolucion:
                    return registro
                raise ValueError("La revisión ya tiene una resolución final")
            # Se reevalúa la instantánea; una aprobación jamás borra sus bloqueos.
            decision = decide(registro.solicitud)
            if resolucion.accion == "aprobar_demo" and (
                    decision.bloqueos or decision.destino == "escalar"):
                raise ValueError("Se requiere corregir evidencia antes de aprobar")
            estado = {"aprobar_demo": "aprobada_demo", "rechazar": "rechazada",
                      "solicitar_correccion": "correccion_solicitada"}[resolucion.accion]
            actualizado = Revision.model_validate({**registro.model_dump(), "estado": estado,
                                                   "resolucion": resolucion.model_dump()})
            self._registros[(tenant, id_)] = actualizado
            return Revision.model_validate(actualizado.model_dump())

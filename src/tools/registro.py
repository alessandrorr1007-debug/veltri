"""Registro de borradores en memoria con partición explícita por tenant."""

from threading import RLock
from typing import Any

from src.knowledge.vectorizacion import validar_tenant
from src.tools.catalogo import Catalogo
from src.tools.pedidos import RegistroDemo


class RegistroPorTenant:
    """Servicio compartido por A7/A8, sin persistencia ni pedidos reales."""

    def __init__(self) -> None:
        self._tenants: dict[str, RegistroDemo] = {}
        self._lock = RLock()

    def registrar(
        self, tenant: str, cliente: str, seleccion: dict[str, int], canal: str, catalogo: Catalogo
    ) -> dict[str, Any]:
        """Hash original intacto; partición tenant externa a la clave de pedido."""
        validar_tenant(tenant)
        with self._lock:
            registro = self._tenants.setdefault(tenant, RegistroDemo())
            return registro.registrar(cliente, seleccion, canal, catalogo)

    def consultar(self, tenant: str, clave: str) -> dict[str, Any] | None:
        """Sin tenant global ni cambios de contexto inducidos por el modelo."""
        validar_tenant(tenant)
        with self._lock:
            registro = self._tenants.get(tenant)
            if registro is None:
                # Valida la clave también cuando no hay registros de ese tenant.
                return RegistroDemo().consultar(clave)
            return registro.consultar(clave)

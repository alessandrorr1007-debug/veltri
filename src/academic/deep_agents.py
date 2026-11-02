"""Deep Agents real con adaptador programado de MockLLM, sin inferencia remota."""

from uuid import uuid4

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool
from pydantic import PrivateAttr

from src.config import Configuracion
from src.core.llm import Modelo, get_llm
from src.schemas.academico import EntradaAcademica, PasoMock
from src.tools.evidencia_academica import revisar_fixture_sintetico


class AdaptadorMock(BaseChatModel):
    """Traduce fixtures tipados del MockLLM a llamadas estándar de herramientas."""

    _mock: Modelo = PrivateAttr()
    _permitidas: set = PrivateAttr(default_factory=set)
    _auditoria: list = PrivateAttr(default_factory=list)
    _rol: str = PrivateAttr(default="")

    def __init__(self, pasos: list[dict], auditoria=None, rol="coordinador"):
        super().__init__()
        self._mock = get_llm(configuracion=Configuracion(usar_mock=True), respuestas=pasos)
        self._auditoria = auditoria if auditoria is not None else []
        self._rol = rol

    @property
    def _llm_type(self):
        return "veltri-mock-academico"

    def bind_tools(self, tools, **kwargs):
        self._permitidas = {
            tool.get("name") if isinstance(tool, dict) else tool.name for tool in tools
        }
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        herramientas = [m for m in messages if isinstance(m, ToolMessage)]
        if any(m.status == "error" for m in herramientas):
            raise ValueError("herramienta_academica_fallida")
        self._auditoria.append({"rol": self._rol, "respuestas_herramientas": [
            {"nombre": m.name, "estado": m.status} for m in herramientas]})
        paso = self._mock.generar("fixture académico", {}, PasoMock)
        llamadas = []
        if paso.herramienta:
            if paso.herramienta not in self._permitidas:
                raise ValueError("herramienta_no_permitida")
            llamadas = [{"name": paso.herramienta, "args": paso.argumentos,
                         "id": str(uuid4()), "type": "tool_call"}]
        return ChatResult(generations=[ChatGeneration(message=AIMessage(
            content=paso.contenido, tool_calls=llamadas))])


def crear_agente(auditoria=None):
    """Construye el framework; task y write_todos son herramientas reales de Deep Agents."""
    from deepagents import create_deep_agent

    herramienta = tool(revisar_fixture_sintetico)

    pasos = [{"herramienta": "write_todos", "argumentos": {"todos": [
        {"content": "Revisar evidencia sintética", "status": "in_progress"},
        {"content": "Explicar bloqueo", "status": "pending"}]}}]
    subagentes = []
    for nombre, descripcion in [
        ("DA-Catalogo", "Revisar evidencia sintética, dominio D3"),
        ("DA-Revision", "Explicar bloqueo de revisión, dominio D4"),
    ]:
        pasos.append({"herramienta": "task", "argumentos": {
            "subagent_type": nombre, "description": descripcion}})
        subagentes.append({"name": nombre, "description": descripcion,
                          "system_prompt": "Solo evidencia sintética; sin efectos comerciales.",
                          "model": AdaptadorMock([
                              {"herramienta": "revisar_fixture_sintetico", "argumentos": {}},
                              {"contenido":
                              '{"sintetico":true,"requiere_revision":true}'}],
                              auditoria=auditoria, rol=nombre),
                          "tools": [herramienta]})
    pasos += [{"herramienta": "write_todos", "argumentos": {"todos": [
        {"content": "Revisar evidencia sintética", "status": "completed"},
        {"content": "Explicar bloqueo", "status": "completed"}]}},
        {"contenido": '{"sintetico":true,"requiere_revision":true,"efecto_comercial":false}'}]
    return create_deep_agent(
        model=AdaptadorMock(pasos, auditoria=auditoria), tools=[], subagents=subagentes,
        system_prompt="DA-CoordinadorAcademico: coordinación académica sin efectos comerciales.",
    )


def ejecutar(entrada: dict, auditoria=None):
    """Solo admite un escenario cerrado; no acepta mensajes arbitrarios."""
    from langsmith import tracing_context

    EntradaAcademica.model_validate(entrada)
    with tracing_context(enabled=False):
        return crear_agente(auditoria).invoke({"messages": [
            {"role": "user", "content": "Revisar fixture sintético académico."}]})

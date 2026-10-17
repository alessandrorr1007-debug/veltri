"""Fábrica única del modelo de lenguaje (Sistema 2).

Regla: ningún otro módulo instancia modelos directamente. Todo pasa por get_llm().
Se implementa en la fase de capa cognitiva: lee LLM_PROVIDER, LLM_MODEL y USE_MOCK_LLM
desde la configuración y devuelve el modelo real o el MockLLM.
"""

from __future__ import annotations

from typing import Any


def get_llm(**opciones: Any) -> Any:
    """Devuelve el modelo configurado (real o simulado). Pendiente de implementar."""
    raise NotImplementedError("get_llm() se implementa en la fase de capa cognitiva")

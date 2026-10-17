"""Configuración y modelos: sin consultas reales, secretos ni coerciones ocultas."""

from types import SimpleNamespace

import pytest
from pydantic import SecretStr, ValidationError

from src.config import Configuracion, cargar_configuracion
from src.core.llm import ErrorModelo, MockLLM, get_llm
from src.schemas.agentes import PlanModelo


def test_configuracion_mock_por_defecto_y_entorno_prevalece(tmp_path):
    ruta = tmp_path / ".env"
    ruta.write_text("USE_MOCK_LLM=0\nLLM_MODEL=modelo-local\nGOOGLE_API_KEY=x\n")
    assert cargar_configuracion(ruta, {}).usar_mock is False
    assert cargar_configuracion(ruta, {"USE_MOCK_LLM": "1"}).usar_mock is True
    assert cargar_configuracion(tmp_path / "ausente", {}).usar_mock is True


def test_configuracion_no_expone_clave_y_rechaza_modo_invalido(tmp_path):
    config = Configuracion(usar_mock=False, modelo="desde-env", clave=SecretStr("x"))
    assert "clave" not in config.model_dump()
    assert "SecretStr" not in repr(config)
    with pytest.raises(ValueError):
        cargar_configuracion(tmp_path / "ausente", {"USE_MOCK_LLM": "true"})
    with pytest.raises(ValidationError):
        Configuracion(usar_mock=False)
    with pytest.raises(ValidationError):
        Configuracion(modelo="../modelo")


def test_factory_mock_sin_fallback_inventado():
    modelo = get_llm(
        configuracion=Configuracion(), respuestas=[{"accion": "stock", "p": 1.0, "c": 1.0}]
    )
    assert isinstance(modelo, MockLLM)
    assert modelo.generar("fixture", {}, PlanModelo).accion == "stock"
    with pytest.raises(ErrorModelo, match="mock_sin_respuestas"):
        modelo.generar("fixture", {}, PlanModelo)


def test_respuesta_malformada_no_expone_contenido():
    modelo = get_llm(
        configuracion=Configuracion(), respuestas=[{"texto": "dato privado sintético"}]
    )
    with pytest.raises(ErrorModelo) as error:
        modelo.generar("fixture", {}, PlanModelo)
    assert str(error.value) == "respuesta_modelo_invalida"


def test_conector_real_con_sdk_y_transporte_simulado(monkeypatch):
    from google import genai

    llamadas = []
    config = Configuracion(usar_mock=False, modelo="desde-env", clave=SecretStr("x"))
    modelo = get_llm(configuracion=config)
    recurso = type(modelo._cliente.interactions)

    def transporte(self, **kwargs):
        llamadas.append(kwargs)
        return SimpleNamespace(output_text='{"accion":"stock","p":0.8,"c":0.7}')

    monkeypatch.setattr(recurso, "create", transporte)
    assert modelo.generar("No calcular", {"tarea": "stock"}, PlanModelo).accion == "stock"
    assert llamadas[0]["model"] == "desde-env"
    assert llamadas[0]["store"] is False
    assert llamadas[0]["response_format"]["mime_type"] == "application/json"
    assert "tools" not in llamadas[0]
    assert modelo.origen_puntuacion == "modelo_no_calibrado"
    assert genai.Client is not None
    modelo._cliente.close()


def test_error_del_proveedor_no_filtra_entrada(monkeypatch):
    config = Configuracion(usar_mock=False, modelo="desde-env", clave=SecretStr("x"))
    modelo = get_llm(configuracion=config)

    def fallar(self, **kwargs):
        raise RuntimeError("dato privado sintético")

    monkeypatch.setattr(type(modelo._cliente.interactions), "create", fallar)
    with pytest.raises(ErrorModelo) as error:
        modelo.generar("fixture", {}, PlanModelo)
    assert str(error.value) == "proveedor_no_disponible_o_respuesta_invalida"
    modelo._cliente.close()

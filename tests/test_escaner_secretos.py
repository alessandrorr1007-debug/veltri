"""El escáner debe cubrir las credenciales del proveedor usado por Veltri."""

import pytest

from scripts.escanear_secretos import escanear


def test_detecta_token_langsmith_sin_revelarlo(tmp_path):
    token = "lsv2_" + "tr_" + "a" * 32 + "_" + "b" * 10
    (tmp_path / "accidental.md").write_text(token, encoding="utf-8")
    hallazgos = escanear(tmp_path)
    assert len(hallazgos) == 1
    assert "Token de LangSmith" in hallazgos[0]
    assert token not in hallazgos[0]


@pytest.mark.parametrize("nombre", [".env", ".env.txt"])
def test_configuracion_privada_no_se_imprime(tmp_path, nombre):
    (tmp_path / nombre).write_text("lsv2_" + "a" * 60, encoding="utf-8")
    assert escanear(tmp_path) == []

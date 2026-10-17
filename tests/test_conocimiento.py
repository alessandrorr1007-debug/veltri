"""Recuperación local, aislamiento, procedencia y reingesta sin modelos ni red."""

import hashlib
import json
import socket
from dataclasses import replace
from pathlib import Path

import pytest

from src.knowledge.almacen import Almacen
from src.knowledge.documentos import DATOS, Fragmento, construir_documentos
from src.knowledge.vectorizacion import validar_texto_publico, vector


@pytest.fixture(scope="module")
def almacen(tmp_path_factory):
    return Almacen(tmp_path_factory.mktemp("rag"))


@pytest.fixture(scope="module")
def corpus():
    return construir_documentos("veltri")


@pytest.fixture(scope="module")
def indexado(almacen, corpus):
    almacen.reemplazar("veltri", corpus)
    return almacen


def fragmento(texto="Contenido de demostración único"):
    return Fragmento("politica:prueba", texto, "data/politicas.md",
                     "data/politicas.md#prueba", hashlib.sha256(texto.encode()).hexdigest())


def test_fragmentacion_completa_con_fuentes_y_hash(corpus):
    assert len([f for f in corpus if f.fuente == "data/catalogo.json"]) == 84
    assert len({f.id for f in corpus}) == len(corpus)
    assert {f.fuente for f in corpus} == {"data/catalogo.json", "data/compatibilidad.json",
                                        "data/politicas.md"}
    for f in corpus:
        hash_actual = hashlib.sha256((DATOS / Path(f.fuente).name).read_bytes()).hexdigest()
        assert f.hash_fuente == hash_actual
        assert f.referencia.startswith(f.fuente + "#")
        assert f.naturaleza == "demostracion_sintetica"


def test_politicas_conservan_contexto_de_propuesta(corpus):
    propuestas = [f for f in corpus if "Cotización válida por 24 horas" in f.texto
                  or "Cotización válida por 24" in f.texto
                  or "Cotización válida" in f.texto]
    # El archivo usa minúscula tras la viñeta; no se depende de un sinónimo del buscador.
    propuestas = propuestas or [f for f in corpus if "válida por 24 horas" in f.texto]
    assert propuestas
    assert all("Propuestas pendientes de aprobación" in f.texto for f in propuestas)


def test_recupera_sku_agotado_con_fuente_correcta(indexado):
    resultados = indexado.buscar("veltri", "CPU-AMD-5500", fuente="data/catalogo.json")
    assert resultados
    primero = resultados[0]
    assert primero["referencia"] == "data/catalogo.json#CPU-AMD-5500"
    producto = json.loads(primero["texto"].split("\n", 1)[1])
    assert producto["sku"] == "CPU-AMD-5500" and producto["stock"] == 0
    assert primero["hash_fuente"]
    assert "distancia" in primero and "confianza" not in primero


def test_recupera_reglas_tecnicas_y_politicas(indexado):
    tecnico = indexado.buscar("veltri", "DDR5 AM5", fuente="data/compatibilidad.json")
    assert tecnico and all(r["fuente"] == "data/compatibilidad.json" for r in tecnico)
    politicas = indexado.buscar("veltri", "pago discrepante revisión humana",
                                fuente="data/politicas.md")
    assert politicas and all(r["fuente"] == "data/politicas.md" for r in politicas)


def test_sin_terminos_comunes_no_inventa_contexto(indexado):
    assert indexado.buscar("veltri", "zxqvunobtainium") == []


@pytest.mark.parametrize("tenant", [None, "", " ", "Veltri", "../otro", 123])
def test_tenant_obligatorio_en_todas_las_operaciones(almacen, corpus, tenant):
    with pytest.raises(ValueError, match="Tenant"):
        almacen.buscar(tenant, "stock")
    with pytest.raises(ValueError, match="Tenant"):
        almacen.contar(tenant)
    with pytest.raises(ValueError, match="Tenant"):
        almacen.reemplazar(tenant, corpus)
    with pytest.raises(ValueError, match="Tenant"):
        construir_documentos(tenant)


def test_omitir_tenant_no_usa_valor_por_defecto(almacen):
    with pytest.raises(TypeError):
        almacen.buscar(consulta="stock")
    with pytest.raises(TypeError):
        almacen.contar()


def test_dos_tenants_no_comparten_datos_ni_cache(almacen):
    uno = fragmento("marcadoralpha motherboard de demostración")
    dos = fragmento("marcadorbeta políticas de demostración")
    almacen.reemplazar("tenant_alpha", [uno])
    almacen.reemplazar("tenant_beta", [dos])
    assert almacen.buscar("tenant_alpha", "marcadoralpha")[0]["texto"] == uno.texto
    assert almacen.buscar("tenant_beta", "marcadoralpha") == []
    assert almacen.buscar("tenant_alpha", "marcadorbeta") == []
    assert almacen.buscar("tenant_beta", "marcadorbeta")[0]["texto"] == dos.texto
    assert almacen.buscar("tenant_inexistente", "marcadoralpha") == []
    assert almacen.contar("tenant_inexistente") == 0
    # Acceso alternado a través de otra instancia en el mismo disco.
    otro = Almacen(almacen._ruta)
    assert otro.buscar("tenant_beta", "marcadoralpha") == []
    assert otro.contar("tenant_alpha") == 1


def test_reingesta_idempotente_y_elimina_obsoletos(almacen):
    primero = fragmento("versionantigua de políticas")
    otro = replace(fragmento("segundodocumento"), id="politica:otro",
                   referencia="data/politicas.md#otro")
    inicial = almacen.reemplazar("actualizacion", [primero, otro])
    repetido = almacen.reemplazar("actualizacion", [otro, primero])
    assert repetido == inicial and almacen.contar("actualizacion") == 2
    nuevo = fragmento("versionnueva de políticas")
    final = almacen.reemplazar("actualizacion", [nuevo])
    assert final["snapshot"] != inicial["snapshot"]
    assert almacen.contar("actualizacion") == 1
    assert almacen.buscar("actualizacion", "versionantigua") == []
    assert almacen.buscar("actualizacion", "segundodocumento") == []
    assert almacen.buscar("actualizacion", "versionnueva")[0]["texto"] == nuevo.texto


@pytest.mark.parametrize("texto", ["correo persona@example.test", "DNI: 12345678",
                                   "RUC: 20123456789", "teléfono: 987654321",
                                   "+51 987 654 321"])
def test_rechaza_pii_sin_exponer_valor(almacen, texto):
    with pytest.raises(ValueError) as error:
        almacen.reemplazar("privacidad", [fragmento(texto)])
    assert texto not in str(error.value)
    with pytest.raises(ValueError) as error:
        almacen.buscar("privacidad", texto)
    assert texto not in str(error.value)
    assert almacen.contar("privacidad") == 0


def test_error_de_ingesta_preserva_snapshot_anterior(almacen):
    valido = fragmento("conservarestado")
    almacen.reemplazar("conservar", [valido])
    with pytest.raises(ValueError):
        almacen.reemplazar("conservar", [valido, valido])
    with pytest.raises(ValueError):
        almacen.reemplazar("conservar", [])
    with pytest.raises(ValueError):
        almacen.reemplazar("conservar", [replace(valido, fuente="pedidos.json")])
    assert almacen.buscar("conservar", "conservarestado")[0]["texto"] == valido.texto


def test_fallo_entre_lotes_no_publica_snapshot_parcial(almacen, corpus, monkeypatch):
    almacen.reemplazar("fallo_lote", [fragmento("estadoanterior")])
    coleccion = almacen._coleccion("fallo_lote")
    tipo = type(coleccion)
    original = tipo.upsert
    llamadas = 0

    def fallar(self, **kwargs):
        nonlocal llamadas
        llamadas += 1
        if llamadas == 2:
            raise RuntimeError("Fallo simulado de escritura")
        return original(self, **kwargs)

    with monkeypatch.context() as parche:
        parche.setattr(tipo, "upsert", fallar)
        with pytest.raises(RuntimeError):
            almacen.reemplazar("fallo_lote", corpus)
    assert almacen.contar("fallo_lote") == 1
    assert almacen.buscar("fallo_lote", "estadoanterior")[0]["texto"] == "estadoanterior"
    almacen.reemplazar("fallo_lote", corpus)
    assert almacen.contar("fallo_lote") == len(corpus)


def test_vectores_reproducibles_y_sin_modelo():
    assert vector("Revisión DDR5") == vector("revision ddr5")
    assert len(vector("AM4")) == 256
    with pytest.raises(ValueError):
        vector("de la y")
    with pytest.raises(ValueError):
        validar_texto_publico("   ")


def test_ingesta_y_busqueda_sin_red(tmp_path, monkeypatch):
    intentos = []

    def prohibido(*args, **kwargs):
        intentos.append(True)
        raise AssertionError("No se permite red en RAG de demostración")

    monkeypatch.setattr(socket.socket, "connect", prohibido)
    monkeypatch.setattr(socket, "create_connection", prohibido)
    almacen = Almacen(tmp_path / "sin_red")
    almacen.reemplazar("offline", [fragmento("localoffline")])
    assert almacen.buscar("offline", "localoffline")
    assert not intentos


@pytest.mark.parametrize("limite", [0, -1, True, 21, 1.5])
def test_limite_invalido(almacen, limite):
    with pytest.raises(ValueError):
        almacen.buscar("veltri", "stock", limite=limite)


def test_fuentes_arbitrarias_no_se_recuperan(almacen):
    with pytest.raises(ValueError):
        almacen.buscar("veltri", "stock", fuente="../../.env")


def test_filtro_metadata_excluye_registro_ajeno_en_coleccion(almacen):
    almacen.reemplazar("filtro_extra", [fragmento("documentopropio")])
    coleccion = almacen._coleccion("filtro_extra")
    coleccion.upsert(ids=["intruso"], documents=["documentoajeno"],
                     embeddings=[vector("documentoajeno")],
                     metadatas=[{"tenant": "otro_tenant", "snapshot": coleccion.metadata["activo"],
                                 "id": "politica:intruso", "fuente": "data/politicas.md"}])
    assert almacen.contar("filtro_extra") == 1
    assert almacen.buscar("filtro_extra", "documentoajeno") == []


def test_coleccion_con_propietario_alterado_falla_cerrada(almacen):
    almacen.reemplazar("propietario", [fragmento("contenido")])
    coleccion = almacen._coleccion("propietario")
    coleccion.modify(metadata={**coleccion.metadata, "tenant": "otro"})
    with pytest.raises(ValueError, match="incompatible"):
        almacen.buscar("propietario", "contenido")
    with pytest.raises(ValueError, match="incompatible"):
        almacen.contar("propietario")


def test_ingesta_solo_lee_tres_archivos_permitidos(tmp_path, corpus):
    for nombre in ("catalogo.json", "compatibilidad.json", "politicas.md"):
        (tmp_path / nombre).write_bytes((DATOS / nombre).read_bytes())
    (tmp_path / "pedidos.json").write_text('correo persona@example.test', encoding="utf-8")
    assert construir_documentos("veltri", tmp_path) == corpus
    with (tmp_path / "politicas.md").open("a", encoding="utf-8") as archivo:
        archivo.write("\ncorreo persona@example.test")
    with pytest.raises(ValueError, match="posible dato personal"):
        construir_documentos("veltri", tmp_path)

# Conocimiento recuperable — FASE 4

Capa de ingesta y recuperación local del futuro RAG. No genera respuestas con LLM,
no implementa agentes ni sustituye las herramientas deterministas. Todos los datos
son sintéticos: ninguna cita autoriza una venta ni confirma precios o stock reales.

## Componentes
- documentos.py: lee únicamente catalogo.json, compatibilidad.json y politicas.md.
  Fragmenta por SKU, relación CPU/placa, sección técnica y bloques de políticas.
  Conserva el encabezado para distinguir propuestas de reglas definidas.
- vectorizacion.py: hashing léxico estable SHA-256 a 256 dimensiones normalizadas;
  sin modelos, API, pesos descargados, ONNX ni inferencia. Colisiones y vocabulario
  limitado son posibles. No es recuperación semántica entrenada ni confianza.
- almacen.py: ChromaDB persistente, una colección por hash del tenant y metadatos
  tenant/snapshot en toda lectura, consulta, escritura y limpieza de documentos.
- ingesta.py: CLI local con --tenant obligatorio. No toma tenant de una variable
  global ni acepta carpetas externas para ampliar el corpus por línea de comandos.

ChromaDB es la dependencia prevista por la arquitectura. Sus dependencias
transitivas incluyen bibliotecas de inferencia y servidor, pero esta fase no las
usa para ejecutar modelos ni abrir servicios. filelock, ya transitiva de Chroma,
se declara directa porque serializa lectores y escritores por tenant entre
instancias y procesos locales. No es un bloqueo distribuido en un filesystem remoto.
Telemetría anonimizada desactivada en Settings; embeddings/documentos de consulta
se proporcionan explícitamente para evitar el embedding por defecto de Chroma.

## Tenant y límites de acceso
Toda operación pública de datos requiere tenant explícito, con formato técnico
[a-z][a-z0-9_]{0,63}. Sin tenant o con valor vacío no hay recuperación ni ingesta.
La colección se deriva de su hash, se verifica su propietario/vectorización y se
filtran documentos tanto por tenant como por snapshot activo. No hay caché global
ni tenant mutable por defecto. Se prueba acceso alternado desde otra instancia.

Esto es aislamiento local por contexto, NO autenticación: quien controla el
filesystem o selecciona un tenant ajeno en el código puede acceder a él. El futuro
backend deberá obtener el tenant de identidad autorizada, nunca del texto del
cliente. No se habilita una API ni se anuncia seguridad multiusuario productiva.

## Ingesta y actualización
Se valida el corpus completo antes de escribir y se generan IDs estables. SHA-256
identifica los bytes de cada fuente; un snapshot incorpora contenido y versión del
vectorizador. Repetir igual contenido y metadatos no crea duplicados. Se escriben
lotes de hasta 128 fragmentos en un snapshot nuevo; al terminar se cambia el activo
y se eliminan versiones anteriores SOLO del mismo tenant. Un fallo antes de la
publicación deja visible el snapshot anterior. Una reingesta correcta limpia
restos de escrituras fallidas. El bloqueo serializa lectores/escritores locales.
No es una transacción entre archivos de origen y Chroma ni un backup del índice.

El directorio generado chroma_db/ está ignorado por Git. Borrar la base o cambiar
el vectorizador requiere reconstrucción desde las tres fuentes. Nunca indexar
pedidos, pagos, solicitudes, conversaciones, .env, logs o datos personales.

## Privacidad y contenido no confiable
Se rechazan patrones de correo, DNI/RUC numérico, teléfonos y asignaciones de
identidad en texto y referencias antes de persistir. Las consultas con esos
patrones también se rechazan; los errores no repiten el valor. No se registran
consultas ni resultados en logs propios. Esta guarda NO detecta todos los nombres
propios o formatos de PII: las fuentes deben seguir siendo datos públicos de demo
revisados. No usarla para sanear documentos de clientes. No se implementa un
clasificador PII ni se afirma una garantía exhaustiva de anonimización.

Los fragmentos son datos no confiables, nunca instrucciones. El filtro anti prompt
injection previo al grafo, su cola DLQ y las pruebas funcionales de CP-2 siguen
pendientes porque no hay grafo ni entrada conversacional ejecutable en esta fase.
La ingesta no ejecuta texto, herramientas, enlaces ni instrucciones del corpus.
No exponer excepciones internas de Chroma como respuestas a usuarios.

## Recuperación y citas
Almacen.buscar(tenant, consulta, limite=5, fuente=None) devuelve una lista limitada
a 20 resultados como máximo. fuente solo puede ser una de las tres fuentes
permitidas. Cada resultado contiene id, texto, fuente, referencia con ancla,
hash_fuente, snapshot, distancia y naturaleza. El índice se consulta con vectores
locales y un filtro de coincidencia léxica descarta candidatos sin términos comunes.
Los SKUs exactos tienen prioridad mediante lectura filtrada del catálogo; después
se ordena por distancia y luego ID. Se recupera un conjunto de candidatos, no un ranking
semántico perfecto. Las consultas con solo palabras vacías son inválidas.

No se inventa respuesta si no hay coincidencias: se devuelve []. Una distancia
vectorial no es probabilidad ni permiso para actuar. La cita de catálogo lleva
SKU exacto; compatibilidad referencia el par o sección; política usa bloque-N
respecto del archivo identificado por hash. Al editar políticas pueden cambiar
los números de bloque: la pareja referencia/hash fija la versión citada.
Las fuentes de precio/stock consultadas en el índice pueden quedar obsoletas:
revalidar con Catalogo y las herramientas antes de cualquier cotización.

## Ejecución en Windows
```powershell
.\.venv\Scripts\python -m pip install -r requirements-fase4.txt
.\.venv\Scripts\Activate.ps1
python -m src.knowledge.ingesta --tenant veltri_tecnologic_pe
python -m pytest tests/test_conocimiento.py -q
python scripts/verificar.py
```

Ejemplo desde Python (no imprime consultas ni texto privado):
```python
from pathlib import Path
from src.knowledge.almacen import Almacen

almacen = Almacen(Path("chroma_db"))
resultados = almacen.buscar("veltri_tecnologic_pe", "CPU-AMD-5500",
                            fuente="data/catalogo.json")
```

API técnica consultada: [cliente Python de Chroma](https://docs.trychroma.com/reference/python).
Pruebas: corpus, citas/SKU, hashes, contextos propuestos, aislamiento, tenant
obligatorio, reingesta, eliminación de obsoletos, fallo entre lotes, persistencia
entre instancias, patrones de PII y operación con sockets de red bloqueados.
No equivalen a evaluar agentes, flujo HITL ni CP-1 a CP-7 integrados.

# Mantenimiento y verificación de Veltri

## Estructura vigente

Instalación y servidor: README principal. `src/` contiene aplicación y módulos académicos; `frontend/` la interfaz; `data/` el corpus sintético; `tests/` regresiones; `evals/` casos dorados; `.agents/` reglas y procedimientos.

`docs/` tiene cuatro guías: índice, arquitectura/referencia técnica, observabilidad y este documento. Se conservan contratos visuales en `agentes/`, JSON Schema de intercambio en `contratos/`, BPMN originales, `evidencias/` y `entrega-semana10/`. No hay que mantener otra guía por fase o auditoría.

## Comprobaciones y scripts

`python scripts/verificar.py` comprueba sintaxis de Python sin generar pyc, existencia de imports internos src/scripts y referencias críticas; después ejecuta pip check, Ruff, pytest y escaneo de secretos. No importa módulos para validar estructura ni escribe evidencias. Las pruebas de CLI incluidas en pytest verifican demos en destinos temporales y protección de originales. `--mypy` sigue opcional: su ausencia no se presenta como aprobación. Pyright se ejecuta separadamente cuando esté instalado, usando `.venv/Scripts/python.exe` como intérprete.

El verificador no acredita cuentas remotas, fidelidad visual de pantallas, corrección tributaria, autonomía de modelos ni integridad de todo el historial Git. Su comprobación de imports internos es estática: los imports dinámicos se cubren mediante ejecuciones y pruebas específicas. No ejecutar operaciones externas para completar una validación local.

Todos los scripts conservan una función única:

- `verificar.py`: controles agregados; `escanear_secretos.py`: escaneo también usado por hook y tests.
- `proteger.py` e `instalar_hooks.py`: protección staged e instalación conservadora del hook.
- `exportar_esquemas.py`: regenera los 35 contratos de intercambio; no es una copia del verificador.
- `demo_academica.py`: LCEL, HITL nativo y Deep Agents con MockLLM; `--salida` debe ser nueva; por defecto usa una ruta temporal. No reemplaza originales.
- `demo_observabilidad.py`: demo local con monitoreo apagado por defecto; no ejecutar --enviar sin autorización nueva.
- `langsmith_segundo_intento.py`: controles de un solo uso y transporte seguro, cubiertos por pruebas. El registro está consumido; no reiniciarlo ni enviarlo otra vez.
- `src/knowledge/ingesta.py`: reconstruye el índice sintético por tenant; usar una ruta temporal durante pruebas.
- `entrega-semana10/generar_informe.py`: reproduce el informe; probar en copia. Los extractos de código pueden diferir tras correcciones, sin autorización para sobrescribir el Word.

No se retiraron scripts activos: ninguno está sustituido ni carece de funcionalidad única. No hay CMD/BAT/PowerShell de proyecto ni HTML generado adicional; `frontend/index.html` es el punto de entrada real.

## Consolidación y recuperación

La revisión estructural del 2/11/2026 retiró 32 archivos: once documentos consolidados, veinte renders/logs de QA reproducibles y un marcador .gitkeep redundante. Las nueve guías de agentes/datos/herramientas/contratos/grafo/decisión/RAG/API/interfaz se integraron en arquitectura. El informe separado de auditoría se resumió aquí y el README de entrega se integró en el índice. Los renders no eran capturas auténticas de la aplicación: se conserva el control de calidad y la recuperación externa.

Respaldo de esta intervención: `C:/Users/aless/AppData/Local/VeltriBackups/estructura-definitiva-20261102-4d9e0a65`. `estado-propio-antes.zip` conserva archivos propios con los cambios parciales previos, sin .env ni almacenamiento privado; `retirados/` conserva las 32 rutas y `plan.json` sus hashes. `inventario.json` clasifica cada archivo, uso, referencias, duplicados y estado Git; `.git`, `.venv` y almacenamiento privado se inventarían sin leer secretos.

Los respaldos de las limpiezas anteriores permanecen fuera del proyecto en VeltriBackups. No restaurar ZIP completos sobre versiones nuevas: recuperar solo la ruta necesaria tras comparar su contenido.

Se preservan las correcciones locales anteriores: tipos de Servicios/RunnableConfig/agentes/LangGraph, escáner de tokens LangSmith y pruebas de CLI. Se instalaron herramientas de análisis solo fuera del repositorio; no se cambiaron dependencias comerciales. No hay commits ni push en esta intervención.

## Evidencias y límites

El Word corregido, generador, figuras, procedencia, BPMN AS-IS/TO-BE y ejecuciones originales permanecen. Las instantáneas del expediente conservan referencias históricas a documentación retirada: son procedencia, no navegación vigente. No se reescriben para aparentar actualidad. El grafo conserva 11 nodos operativos, 13 vértices y 20 aristas.

La auditoría previa dejó 473 pruebas aprobadas, Pyright 90 archivos sin errores, imports y demos correctos. Corrigió el script académico y añadió nueve regresiones; el generador se verificó en copia y los originales por hash. Las correcciones actuales añaden cuatro pruebas estructurales del verificador.

Resultado posterior a esta consolidación: **477 pruebas aprobadas**, cero fallos/errores/omitidas y dos advertencias de dependencias (125,79 segundos de pytest). Ruff, dependencias y secretos OK. Pyright: 91 archivos, cero errores/advertencias; compilación e imports correctos. Demo LCEL/HITL/Deep Agents, grafo 13 vértices/20 aristas, API, exportación idéntica de 35 esquemas y generador en copia: correctos. Enlaces vigentes y referencias activas a retirados: cero rotos. Los 134 archivos protegidos conservan sus hashes.

Se revisaron 247 archivos propios y se inventariaron 16.167 archivos incluidos administración y dependencias. Se conservaron 215 archivos propios iniciales; el nuevo test del verificador deja 216. `docs/` pasó de 126 a 94 archivos. No se confunde inventariar librerías del entorno con auditar semánticamente su implementación. El inventario externo permite consultar cada clasificación A–F y las razones de conservación/retirada.

LangSmith sigue pendiente de acreditación visual de la traza remota previa. HTTP 202 no la acredita. No se usa ninguna clave real ni se envían trazas en la validación. La guarda de PII por patrones y el aislamiento por tenant no sustituyen autenticación productiva.

## Conservados con motivo concreto

Los 35 JSON Schema son generados, pero constituyen el contrato entregable de intercambio además de los validadores Python: se mantienen junto al exportador. Los nueve diagramas por agente son contratos visuales exigidos por el workflow, no copias de la arquitectura general. Los originales de evidencias, aunque históricos, acreditan ejecuciones distintas. `.env`, `.env.txt` y `chroma_db/` son privados y no se limpian.

No se identificaron archivos ambiguos adicionales que requieran retirada. BPMN AS-IS conserva la única comparación del proceso previo y las skills siguen requeridas por GEMINI.md. Eliminar esos alcances requiere decisión del usuario.

## Resumen de tres líneas

Consolidamos la referencia técnica y retiramos material reproducible con respaldo verificado.
El verificador ahora comprueba estructura y dependencias, además de calidad, pruebas y secretos.
Conservamos correcciones, evidencias académicas y datos privados sin publicar ni enviar trazas.

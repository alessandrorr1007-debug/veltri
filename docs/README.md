# Documentación de Veltri

## Estado actual y ejecución

La instalación vigente está en [README principal](../README.md): `requirements.txt` para aplicación y módulos académicos, `requirements-dev.txt` para pruebas y generación Word. `requirements-academico.txt` es un alias compatible, sin versiones independientes.

- Aplicación: `src/api/`, `frontend/`; agentes: `src/agents/`; herramientas: `src/tools/`.
- Orquestación: `src/graph/`; contratos: `src/schemas/`; configuración: `src/config.py`.
- Demostraciones académicas: `src/academic/`, `scripts/demo_academica.py`.
- Verificación: `tests/`, `scripts/verificar.py`.
- [Arquitectura](arquitectura.md), [agentes](agentes.md), [grafo](grafo.md), [observabilidad](observabilidad.md).

## Entrega Semana 10

- [Informe Word de 17 páginas](entrega-semana10/Veltri_Semana10_Informe_Academico.docx) y [generador](entrega-semana10/generar_informe.py).
- [Auditoría académica](auditoria-final-semana10.md), [expediente](evidencias/), [resumen JSON](evidencias-semana10.json).
- Los BPMN originales y todos los registros académicos se conservan.
- Pendientes académicos: capturas auténticas y acreditación visual de una traza LangSmith verificada. HTTP 202 no acredita una traza completa.

## Lectura histórica

Los documentos titulados por fases, `LEEME_entorno.md`, los informes de auditoría anteriores y las instantáneas del expediente describen estados históricos. Sus afirmaciones de implementación y comandos se interpretan en su fecha; para instalar ahora se usa el README principal. Las menciones antiguas a ausencia de Deep Agents no describen `src/academic/deep_agents.py` actual. `claude/` es la plantilla de referencia conservada; no debe copiarse sobre el proyecto actual automáticamente.

## Mantenimiento

[Informe de limpieza del 2 de noviembre de 2026](mantenimiento/limpieza-20261102.md) e [inventario clasificado](mantenimiento/inventario-20261102.json).

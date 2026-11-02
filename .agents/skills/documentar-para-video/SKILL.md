---
name: documentar-para-video
description: Úsalo siempre que se complete una fase o funcionalidad, y al preparar el README, los diagramas o el material para el video de la práctica calificada.
---

# Documentar para el video

El video muestra el paso a paso del desarrollo hasta el código. Esta skill deja material listo en cada fase.

## Al cerrar cada fase
1. Resumen de **3 líneas en lenguaje simple**: qué se hizo, por qué y qué sigue. Debe poder leerse en voz alta.
2. Actualiza `docs/arquitectura.md` (diagrama Mermaid) si cambió la arquitectura.
3. Mantén en `docs/README.md` las demostraciones vigentes. Crea un guion solo si el usuario pide un video; no acumules guiones históricos.
4. Si la fase tiene interfaz, indica cuándo tomar capturas del antes y el después.
5. Actualiza `.agents/rules/estructura-y-comandos.md` si apareció una carpeta o un comando nuevo.

## README
Mantenlo en español con: qué es, problema, arquitectura, agentes A1 a A8, HITL, casos CP-1 a CP-7, instalación en Windows, estructura, **Uso de IA** (declaración de asistentes usados y de que el equipo responde por lo entregado) y aviso de que los precios son de ejemplo.

## Orden sugerido del video
Problema, arquitectura por capas, entorno agéntico (reglas, workflows, skills), almacén de conocimiento, agentes, decisión y HITL, orquestador, interfaz, pruebas y demo final.

## Checklist final
- [ ] Resumen de 3 líneas entregado.
- [ ] Índice de demostraciones y diagrama al día.
- [ ] README coherente con el código real.

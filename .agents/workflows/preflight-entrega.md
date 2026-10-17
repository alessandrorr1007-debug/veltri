---
description: Verificación final antes de entregar o subir a GitHub (solo se ejecuta cuando yo lo pido)
---

# /preflight-entrega

Úsalo únicamente cuando yo lo pida explícitamente. Solo verifica y reporta; no subas nada a GitHub sin mi OK.

1. **Verificación.** Ejecuta `python scripts/verificar.py` y muestra la salida real. Debe terminar en verde.
2. **Secretos.** Confirma que el escaneo no tiene hallazgos y que `.env` no está en `git status`.
3. **Estructura.** Compara el árbol real con `.agents/rules/estructura-y-comandos.md`. Reporta archivos fuera de lugar, carpetas sin `__init__.py`, código muerto e imports sin usar.
4. **README.** Confirma que están todas las secciones: qué es, problema, arquitectura con Mermaid, agentes A1 a A8, HITL, casos CP-1 a CP-7, instalación en Windows, estructura, Uso de IA y aviso de precios de ejemplo.
5. **Documentos.** Confirma que `docs/arquitectura.md` y `docs/guion-video.md` están al día.
6. **Comandos.** Verifica que cada comando de la regla de estructura realmente exista y funcione.
7. **Git.** Muestra `git status` y la lista de archivos que se subirían. Confirma que el hook pre-commit está instalado.
8. **Reporte.** Tabla de pasos con OK o pendiente. Si todo está OK, pregúntame si hacemos el commit y el push al remoto. Nunca uses `push --force`.

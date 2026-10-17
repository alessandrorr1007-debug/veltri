---
description: Revisa seguridad y privacidad: prompt injection, tenant, datos personales y secretos
---

# /revision-seguridad

Úsalo antes de cerrar una fase que toque entrada de datos, almacén RAG, API o logs. Solo lee y reporta; no corrijas nada sin mi OK.

1. **Aislamiento por tenant.** Revisa que todo acceso al almacén RAG reciba un tenant explícito y que no exista una ruta que recupere sin él. Revisa también caches y variables globales que puedan sobrevivir entre peticiones.
2. **Filtro anti prompt injection.** Confirma que corre ANTES del grafo y que un mensaje sospechoso va a la cola de fallidos sin llegar a ningún agente. Prueba con el caso CP-2 y con dos variantes nuevas.
3. **Datos personales.** Confirma que DNI, RUC, teléfono y correo no se indexan en el almacén ni aparecen en logs, trazas ni mensajes de error. Busca con búsqueda de texto cualquier `print` o log que los exponga.
4. **Secretos.** Ejecuta `python scripts/escanear_secretos.py`. Confirma que `.env` está en `.gitignore` y que `.env.example` no trae valores.
5. **Salida.** Confirma que la API nunca devuelve el prompt del sistema, claves ni trazas internas con datos sensibles.
6. **Reporte.** Lista de hallazgos con gravedad (alta, media, baja), archivo y línea, y la corrección propuesta. Si hay una clave real expuesta, DETENTE y avísame de inmediato.

# Entorno de Veltri Tecnologic

Este paquete prepara el desarrollo; no contiene el sistema terminado.
La carpeta claude se conserva como referencia. No se detecta automáticamente
como configuración de Antigravity ni equivale a la carpeta .claude de Claude Code.

## Contenido
- GEMINI.md: las diez reglas originales.
- AGENTS.md: orientación para leer el paquete.
- hooks/: protección, verificación, escaneo e instalación del hook de Git.
- skills/comandos/: cinco procedimientos para instalar como workflows.
- skills/conocimiento/: dos skills, cada una con su SKILL.md.
- skills/reglas/: estructura prevista del proyecto.
- plantilla/: esqueleto, pruebas, evaluaciones y configuración originales.
- .mcp.json: sin servidores. settings.json: configuración documental propia.

## Preparación del proyecto
Desde D:\Proyectos\veltri-orquestador, pide al agente:

```text
Lee claude/AGENTS.md, claude/GEMINI.md y este LEEME.
Prepara únicamente el entorno. Antes de copiar, comprueba colisiones y conserva
los archivos existentes. Copia el contenido de claude/plantilla/ a la raíz.
Copia claude/skills/comandos/ a .agents/workflows/;
claude/skills/conocimiento/ a .agents/skills/ y claude/skills/reglas/ a .agents/rules/.
Los scripts ya vienen en plantilla/scripts/ y deben coincidir con claude/hooks/.
Conserva claude/ como referencia. No copies su AGENTS.md sobre el de la plantilla.
No copies settings.json ni .mcp.json a una ubicación del IDE sin comprobar su formato.
Confirma las reglas y ejecuta las verificaciones. No crees todavía catálogo,
agentes, API ni interfaz. Espera la indicación de la primera fase.
```

La detección de .agents y GEMINI.md depende de la versión del IDE: comprueba
Rules, Workflows y Skills en la herramienta antes de asumir que están activos.
Si no aparecen, usa sus paneles o sigue los procedimientos leyendo los archivos.
Este paquete no instala hooks de eventos del IDE.

## Python y verificación
En la raíz instalada, usa PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python scripts/verificar.py
git init
.\.venv\Scripts\python scripts/instalar_hooks.py
```
Desde el paquete sin instalar: `python claude/hooks/verificar.py` comprueba
claude/plantilla. Los scripts resuelven rutas desde su ubicación.
El instalador solo acepta un repositorio cuya raíz sea la plantilla o el proyecto
instalado; no modifica el repositorio de una carpeta superior ni hooks ajenos.
Reinstala el hook si cambias la ubicación del proyecto o del intérprete Python.

El hook comprueba modificaciones y eliminaciones de archivos protegidos antes del
commit y busca patrones de secretos en archivos de trabajo. No impide editar
archivos, no examina exhaustivamente todos los secretos y no sustituye revisión
del contenido staged. Las adiciones iniciales de archivos protegidos se permiten.
Para un cambio protegido previamente autorizado, define temporalmente
VELTRI_AUTORIZO_CAMBIO_PROTEGIDO=1 y elimina la variable después del commit.

## Desarrollo posterior
Las fases previstas son datos, herramientas deterministas, esquemas Pydantic,
RAG, decisión y revisión humana, agentes, grafo, API, interfaz y entrega.
Espera un “continúa” entre fases. Los precios serán ejemplos, no cotizaciones reales.
El README y los casos CP-1 a CP-7 son borradores; no demuestran funcionalidad
implementada. El escáner y las pruebas iniciales verifican solo el entorno.

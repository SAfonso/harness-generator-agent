---
name: harness-agents
description: "Genera un harness multi-agente personalizado para Claude Code entrevistando (o inspeccionando, en proyectos ya empezados) el proyecto actual. Usa esta skill cuando el usuario pida montar el harness, generar agentes o preparar un proyecto para trabajar con esta metodología."
---

# /harness-agents

Arranca el generador de harness (`harness-generator-agent`) sobre el proyecto actual.
No vendoriza el código — referencia el repo clonado por su ruta relativa.

## Antes de arrancar

Comprueba que `pydantic` y `jinja2` están disponibles en el intérprete activo.
Si falta alguna, instálala antes de continuar (nunca asumas que ya están):

```bash
python3 -c "import pydantic, jinja2" 2>/dev/null || pip install pydantic jinja2
```

## Arranque

Desde la raíz del repo clonado de `harness-generator-agent`:

```bash
python3 -m src.main
```

El menú interactivo pide elegir modo (`EJECUTOR`/`PROFESOR`) y describir el
proyecto. Si el directorio de salida ya es un proyecto empezado, el propio
pipeline lo detecta e inspecciona antes de preguntar (ver `specs/main.md`,
`specs/tools.md#inspect_project`). El harness resultante queda en `harness/`
dentro del directorio de salida elegido.

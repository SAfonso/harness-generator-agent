---
name: harness-agents
description: "Genera un harness multi-agente personalizado para Claude Code entrevistando (o inspeccionando, en proyectos ya empezados) el proyecto actual. Usa esta skill cuando el usuario pida montar el harness, generar agentes o preparar un proyecto para trabajar con esta metodología."
---

# /harness-agents

Arranca el generador de harness (`harness-generator-agent`) sobre **el
proyecto actual** — el directorio desde el que se invoca esta skill, nunca el
repo del generador. Esto importa: el generador usa el directorio de trabajo
en el momento de ejecutarse como destino (dónde inspecciona y dónde escribe
`harness/`), así que el comando final debe lanzarse con el `cwd` puesto en el
proyecto del usuario.

## Antes de arrancar

1. Comprueba si el comando `harness-agents` ya está disponible:
   ```bash
   command -v harness-agents
   ```
2. Si no lo está, instálalo en modo editable desde el repo clonado del
   generador (`pydantic`/`jinja2` se instalan solos como dependencias
   declaradas en su `pyproject.toml`):
   ```bash
   pip install -e /ruta/al/repo/harness-generator-agent
   ```

**Nunca** ejecutes `python3 -m src.main` directamente como atajo: exige que el
`cwd` esté en la raíz del propio repo del generador para que `import src`
resuelva, y eso pondría el harness generado dentro del repo del generador en
vez de en el proyecto del usuario — justo lo que rompe el caso de uso
brownfield. El entry point instalado no tiene ese problema: funciona desde
cualquier directorio.

## Arranque

Con el `cwd` ya en la raíz del proyecto del usuario (nunca en el repo del
generador):

```bash
harness-agents
```

El menú interactivo pide elegir modo (`EJECUTOR`/`PROFESOR`) y describir el
proyecto. Si el directorio ya es un proyecto empezado, el propio pipeline lo
detecta e inspecciona antes de preguntar — infiere lo que puede con evidencia
y audita problemas mecánicos (sin repo/remoto git, sin CI, sin tests,
documentación vacía), que entran como tareas iniciales del backlog generado
(ver `specs/tools.md#inspect_project`). El harness resultante queda en
`harness/` dentro del proyecto.

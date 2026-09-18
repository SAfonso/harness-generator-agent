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

## Arranque — nunca invoques `harness-agents` a secas

`harness-agents` sin `--text` es un menú interactivo con `input()`. Eso
funciona si un humano lo teclea en su propia terminal, pero **revienta con
`EOFError`** en cuanto lo ejecuta el tool de Bash de un agente: un
subproceso lanzado por Bash no sostiene una conversación de stdin turno a
turno, así que el primer `input()` encuentra el flujo ya cerrado. Esta skill
existe precisamente para evitarlo: **Claude es la capa conversacional, no el
subproceso.**

1. Pregunta al usuario en el propio chat lo que describe su proyecto (tipo,
   stack, fuentes de datos, restricciones, criterios de aceptación,
   entregable, tiempo disponible) — o, si el proyecto ya existe, deja que la
   inspección brownfield del paso 2 rellene lo que pueda inferir y pregunta
   solo el resto.
2. Con el `cwd` ya en la raíz del proyecto del usuario (nunca en el repo del
   generador), ejecuta:
   ```bash
   harness-agents --text "<descripción reunida en el chat>" --mode EJECUTOR --output-dir "$(pwd)"
   ```
   (`--mode PROFESOR` en vez de `EJECUTOR` si el usuario quiere que le reten
   las decisiones poco pensadas — ver `specs/intake_agent.md`.)
3. Si el comando termina con código de salida distinto de cero y la salida
   incluye "Falta información sobre estas dimensiones", pregunta al usuario
   por cada una en el chat, amplía el `--text` con las respuestas, y vuelve
   a ejecutar el mismo comando — es una invocación nueva, no una
   continuación de la anterior.
4. Si el proyecto ya es uno empezado, el propio pipeline lo detecta e
   inspecciona antes de completar el paso 1 — infiere lo que puede con
   evidencia y audita problemas mecánicos (sin repo/remoto git, sin CI, sin
   tests, documentación vacía, un `CLAUDE.md` existente), que entran como
   tareas iniciales del backlog generado (ver `specs/tools.md#inspect_project`).

Si el validator aprueba, el harness se aplica **directamente en la raíz del
proyecto** — `.claude/agents/`, `AGENTS.md`, `CHECKPOINTS.md`,
`feature_list.json`, `init.sh`, `progress/` — sin copiar ni mover nada a
mano. Solo `CLAUDE.md` se protege: si ya existe uno, el generado queda como
`CLAUDE.harness.md` junto al tuyo en vez de sobrescribirlo
(`specs/tools.md#apply_harness`) — dile al usuario que lo fusione a mano
cuando pase esto. Nota: no está verificado si Claude Code necesita una
sesión nueva para detectar agentes recién escritos en `.claude/agents/` —
si el usuario pide usar un agente del harness (ej. "arranca con el leader")
y no aparece disponible, sugiérele reabrir la sesión antes de asumir que
algo falló.

# CLAUDE.md — harness-generator-agent

Este fichero solo contiene reglas generales y redirección. El detalle de cada
módulo está en su spec.

## Reglas generales

1. **No leas specs de módulos que no toques.** Ve directo al spec del módulo
   sobre el que estás trabajando.
2. **SDD:** nada se implementa sin estar en el spec de su módulo. Si falta,
   sigue el protocolo de spec faltante (más abajo) antes de escribir código.
3. **TDD:** test primero, implementación después — sin excepciones.
4. **Orden por tarea:** actualizar spec del módulo → escribir test → implementar → commit.
5. Lo transversal (arquitectura, modos, criterios de aceptación, convenciones de
   testing) está en `SPEC.md`. Léelo una vez por sesión; para el resto, ve directo
   al spec del módulo.
6. Tests: pytest, fixture `tmp_path` para filesystem, `monkeypatch` para variables
   de módulo. Ejecuta `python3 -m pytest tests/ -q` antes de cada commit.

## ¿En qué módulo vas a trabajar?

| Si tocas… | Lee su spec | Y sus errores conocidos |
|---|---|---|
| `src/models/` | `specs/models.md` | `errors/models.md` |
| `src/tools/` | `specs/tools.md` | `errors/tools.md` |
| `src/agents/intake_agent.py` | `specs/intake_agent.md` | `errors/intake_agent.md` |
| `src/agents/analysis_agent.py` | `specs/analysis_agent.md` | `errors/analysis_agent.md` |
| `src/agents/generator_agent.py` | `specs/generator_agent.md` | `errors/generator_agent.md` |
| `src/agents/validator_agent.py` | `specs/validator_agent.md` | `errors/validator_agent.md` |
| `src/templates/` | `specs/templates.md` | `errors/templates.md` |
| `src/main.py` | `specs/main.md` | `errors/main.md` |
| `pyproject.toml`, `skill/` | `specs/packaging.md` | `errors/packaging.md` |

Si el archivo que tocas no aparece en esta tabla, es un módulo nuevo: sigue el
protocolo de spec faltante antes de implementar, y añade la fila correspondiente.

## Cuando falta spec (módulo nuevo o gap)

Adopta el modo PROFESOR (mismo espíritu que `intake_agent`, ver
`ONBOARDING.md §3.1`): no rellenes contenido de spec por tu cuenta. Pregunta
al usuario el comportamiento esperado, casos límite y restricciones antes de
crear o actualizar un spec — sin aceptar vaguedad, igual que PROFESOR no
avanza con huecos.

Nota: esto es un préstamo de comportamiento, no una llamada a
`intake_agent.py` — ese código resuelve las 7 dimensiones del proyecto que
el harness *genera* (Sistema A), no gaps en los specs internos de este
repo. Dominios distintos, aunque el nombre en clave sea el mismo.

Aplica tanto a módulos sin spec (regla 2) como a gaps revelados por un error
(protocolo de errores, paso 3).

## Protocolo de errores (obligatorio)

Cuando aparezca un error durante una tarea en un módulo:

1. Lee `errors/<modulo>.md` y después `errors/ERRORS.md` (transversales).
2. **Si el error ya está registrado** → aplica la solución documentada. No
   re-investigues desde cero.
3. **Si es nuevo** → resuélvelo y, antes de cerrar la tarea, regístralo:
   - específico del módulo → `errors/<modulo>.md`
   - transversal (≥ 2 módulos o entorno) → `errors/ERRORS.md`
   El formato de entrada está definido en `errors/ERRORS.md`.
   Si el error revela un gap o inconsistencia en el spec del módulo (no solo
   en la implementación), sigue el protocolo de spec faltante — no lo
   rellenes tú directamente. El registro de errores documenta el parche,
   pero el spec sigue siendo la fuente de verdad.

Objetivo: un mismo error nunca se investiga dos veces.

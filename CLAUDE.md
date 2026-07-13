# CLAUDE.md — harness-generator-agent

Este fichero solo contiene reglas generales y redirección. El detalle de cada
módulo está en su spec — **no leas specs de módulos que no toques**.

## Reglas generales

1. **SDD:** nada se implementa sin estar en el spec de su módulo. Si falta, actualiza
   el spec primero.
2. **TDD:** test primero, implementación después — sin excepciones.
3. **Orden por tarea:** actualizar spec del módulo → escribir test → implementar → commit.
4. Lo transversal (arquitectura, modos, criterios de aceptación, convenciones de
   testing) está en `SPEC.md`. Léelo una vez por sesión; para el resto, ve directo
   al spec del módulo.
5. Tests: pytest, fixture `tmp_path` para filesystem, `monkeypatch` para variables
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

## Protocolo de errores (obligatorio)

Cuando aparezca un error durante una tarea en un módulo:

1. Lee `errors/<modulo>.md` y después `errors/ERRORS.md` (transversales).
2. **Si el error ya está registrado** → aplica la solución documentada. No
   re-investigues desde cero.
3. **Si es nuevo** → resuélvelo y, antes de cerrar la tarea, regístralo:
   - específico del módulo → `errors/<modulo>.md`
   - transversal (≥ 2 módulos o entorno) → `errors/ERRORS.md`
   El formato de entrada está definido en `errors/ERRORS.md`.

Objetivo: un mismo error nunca se investiga dos veces.

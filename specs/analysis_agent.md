# SPEC — `analysis_agent` (modo JUEZ)

> Código: `src/agents/analysis_agent.py` · Tests: `tests/test_analysis_agent.py`
> Errores conocidos: `errors/analysis_agent.md` · Reglas transversales: `SPEC.md`
> Depende de: `specs/models.md` (HarnessSpec, AgentRole), `specs/tools.md` (classify_project, update_spec)

## Responsabilidad

Tomar la `HarnessSpec` parcial y decidir la estructura completa del harness:
cuántos agentes, qué roles, qué modos, qué reglas.

## Firma

```python
run_analysis(spec: HarnessSpec) -> HarnessSpec
```

## Flujo interno

1. Recibe `HarnessSpec` parcial de `intake_agent`
2. Llama a `classify_project()` para confirmar tipo
3. Aplica reglas de decisión por tipo de proyecto (tabla abajo)
4. Decide `harness_complexity` según tiempo disponible y scope
5. Construye lista de `AgentRole` con modos asignados
6. Genera lista de reglas específicas del harness
7. Devuelve `HarnessSpec` completa

## Tools disponibles

- `classify_project()`
- `update_spec()` (v2)

## Reglas de composición de agentes

**El conjunto de agentes del harness es fijo — no se inventan agentes nuevos por
tipo de proyecto.** Los roles definidos en la tabla de modos de `SPEC.md` son los
mínimos que están **siempre**, sea cual sea el tipo:

| Agente | Modo | Presencia |
|---|---|---|
| leader | DIRECTOR | Siempre — orquesta la ejecución del harness |
| planner | ARQUITECTO | Siempre — descompone objetivos en tareas atómicas y asigna complejidad |
| implementer | BISTURÍ | Siempre |
| reviewer | FISCAL | Siempre |
| tester | QA | Solo proyectos de tipo `agent` (según su propia definición en la tabla de modos) |

Los datos viven en `src/config.py` (`MIN_AGENTS_BY_TYPE` — todas las entradas
contienen el núcleo fijo; el tipo `agent` añade `tester`).

> Decisión de diseño (2026-07-13): descartada la idea inicial de agentes extra
> por tipo (`data_validator`, `security_checker`, `ux_checker`). El harness no
> añade agentes distintos de los definidos.

## Reglas generadas: tareas atómicas y modelo por complejidad

`_build_rules()` incluye siempre (además de las reglas por complejidad del harness):

- **Tareas atómicas:** cada tarea del backlog es una unidad corta y acotada con un
  único entregable verificable. Objetivos amplios ("hazme el front") no entran al
  backlog: el planner los descompone primero.
- **Modelo por complejidad de tarea:** cada tarea lleva `complejidad`
  (`alta | media | baja`) asignada por el planner, y el leader la lanza con el
  modelo del tier correspondiente (ver `MODEL_TIER_BY_COMPLEXITY` en `src/config.py`):
  `alta` (planificar, documentar, diseñar) → modelo potente; `media`
  (implementación estándar) → modelo intermedio; `baja` (tareas mecánicas)
  → modelo económico.

## Reglas de modo JUEZ

```
- Decide con criterios explícitos, no por intuición
- Justifica cada rol añadido en una línea
- Si hay ambigüedad en el input, resuélvela con la opción más conservadora
- No añadas agentes por si acaso — cada rol tiene que ganarse su sitio
```

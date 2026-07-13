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

## Reglas de decisión por tipo

Los datos viven en `src/config.py` (`MIN_AGENTS_BY_TYPE`):

| Tipo | Agentes mínimos | Consideraciones |
|---|---|---|
| data_pipeline | implementer, reviewer | Añadir data_validator si hay transformaciones complejas |
| api | implementer, reviewer | Añadir security_checker si hay auth |
| web | implementer, reviewer | Añadir ux_checker si hay criterios visuales |
| agent | implementer, reviewer, tester | Siempre añadir tester para loops de agente |
| cli | implementer, reviewer | Harness más simple por defecto |

## Reglas de modo JUEZ

```
- Decide con criterios explícitos, no por intuición
- Justifica cada rol añadido en una línea
- Si hay ambigüedad en el input, resuélvela con la opción más conservadora
- No añadas agentes por si acaso — cada rol tiene que ganarse su sitio
```

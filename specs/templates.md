# SPEC — módulo `templates`

> Código: `src/templates/` · Tests: `tests/test_render_template.py` (vía la tool)
> Errores conocidos: `errors/templates.md` · Reglas transversales: `SPEC.md`

## Responsabilidad

Plantillas Jinja2 que `generator_agent` renderiza (vía `render_template`) para
producir los ficheros del harness.

## Estructura

```
src/templates/
├── base/                 # Plantillas compartidas por todos los tipos
│   ├── CLAUDE.md.j2
│   ├── AGENTS.md.j2
│   ├── CHECKPOINTS.md.j2
│   ├── feature_list.json.j2
│   ├── init.sh.j2
│   └── ledger.json.j2    # v2, spec — ledger vacío ({"decisions": [], "tasks": []})
└── agents/               # Plantillas de agentes con modos
    ├── leader.md.j2      # modo: DIRECTOR
    ├── planner.md.j2     # modo: ARQUITECTO — tareas atómicas + complejidad
    ├── intake.md.j2      # modo: PROFESOR
    ├── analysis.md.j2    # modo: JUEZ
    ├── generator.md.j2   # modo: ESCRIBANO
    ├── implementer.md.j2 # modo: BISTURÍ
    ├── reviewer.md.j2    # modo: FISCAL
    ├── notario.md.j2     # v2, spec — modo: NOTARIO, rama + commit/push/PR
    ├── centinela.md.j2   # v2, spec — modo: CENTINELA, CI + merge automático
    └── tester.md.j2      # modo: QA — solo proyectos de tipo agent
```

## Convenciones

- Formato: Jinja2 (`.j2`)
- Variables disponibles en todas las plantillas: `{{ spec }}` (HarnessSpec completa)
- Las plantillas de agente tienen acceso a `{{ agent }}` (AgentRole específico)
- Las plantillas NO contienen lógica compleja — eso va en los agentes
- Ninguna plantilla renderizada puede dejar `{{` sin resolver (check 7 del validator)
- Cada tarea de `feature_list.json.j2` lleva el campo `complejidad`
  (`alta | media | baja`) — determina el modelo con que el leader la lanza
- El backlog semilla no contiene objetivos amplios: el entregable entra como
  tarea de **descomposición** asignada al planner, no como tarea de implementación

## v2 (spec, sin implementar) — NOTARIO, CENTINELA y ledger

- `notario.md.j2` describe **dos** momentos, en secciones separadas dentro del
  mismo fichero: `## Al iniciar la tarea` (crea `task/{id}-{slug}` desde la rama
  por defecto del remoto, detectada, no hardcodeada) y `## Al cerrar la tarea`
  (commit + push de esa rama + abre/actualiza el PR, solo tras aprobación de
  FISCAL/QA)
- `centinela.md.j2` especifica que verifica CI y conflictos, y si están en verde
  hace **merge automático** del PR — no espera aprobación humana (el batch corre
  desatendido); si falla, reconstruye el contexto y lo entrega a FISCAL, nunca
  relanza BISTURÍ directamente ni repite la tarea entera
- `ledger.json.j2` se genera **vacío** (`{"decisions": [], "tasks": []}`) —
  `generator_agent` lo escribe una sola vez; a partir de ahí lo actualiza DIRECTOR
  en runtime, no se vuelve a renderizar
- NOTARIO y CENTINELA son núcleo fijo: se generan para todos los tipos de
  proyecto, igual que implementer/reviewer (ver `specs/generator_agent.md` y
  `config.py#_CORE_AGENTS`)
- Ver el flujo completo de ejecución en `SPEC.md#flujo-de-ejecución-del-harness-generado`

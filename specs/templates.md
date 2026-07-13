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
│   └── init.sh.j2
└── agents/               # Plantillas de agentes con modos
    ├── leader.md.j2      # modo: DIRECTOR
    ├── intake.md.j2      # modo: PROFESOR
    ├── analysis.md.j2    # modo: JUEZ
    ├── generator.md.j2   # modo: ESCRIBANO
    ├── implementer.md.j2 # modo: BISTURÍ
    ├── reviewer.md.j2    # modo: FISCAL
    └── tester.md.j2      # modo: QA — solo proyectos de tipo agent
```

## Convenciones

- Formato: Jinja2 (`.j2`)
- Variables disponibles en todas las plantillas: `{{ spec }}` (HarnessSpec completa)
- Las plantillas de agente tienen acceso a `{{ agent }}` (AgentRole específico)
- Las plantillas NO contienen lógica compleja — eso va en los agentes
- Ninguna plantilla renderizada puede dejar `{{` sin resolver (check 7 del validator)

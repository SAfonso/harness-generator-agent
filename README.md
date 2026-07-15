# HarnessAgents

Sistema multi-agente que te entrevista sobre tu proyecto y genera un **harness
personalizado para Claude Code**: `CLAUDE.md`, agentes con modos, backlog de
tareas atómicas, criterios de validación y verificación de entorno — listos
para usar sin modificaciones.

## Cómo funciona

```
input del usuario
   │
   ▼
intake_agent (PROFESOR) ──► analysis_agent (JUEZ) ──► generator_agent (ESCRIBANO) ──► validator_agent (FISCAL)
   entrevista las 7            decide estructura,        renderiza los ficheros        veredicto: 7 checks
   dimensiones del             complejidad y reglas      del harness (Jinja2)          de coherencia
   proyecto                                │
                                           ▼
                              HarnessSpec (estado compartido)
```

Los cuatro agentes se comunican a través de una única estructura (`HarnessSpec`)
y se orquestan desde `main.py`.

## El harness generado

```
harness/
├── CLAUDE.md              # Modo, reglas y política de modelos — lo primero que lee Claude Code
├── AGENTS.md              # Mapa de roles
├── CHECKPOINTS.md         # Criterios de aceptación para el reviewer
├── feature_list.json      # Backlog de tareas atómicas con complejidad (alta|media|baja)
├── init.sh                # Verificación del entorno
└── .claude/agents/
    ├── leader.md          # DIRECTOR — orquesta, evalúa rechazos, escala al usuario
    ├── planner.md         # ARQUITECTO — descompone objetivos en tareas atómicas
    ├── implementer.md     # BISTURÍ — implementa sin salirse del scope
    ├── reviewer.md        # FISCAL — aprueba/rechaza contra CHECKPOINTS.md
    └── tester.md          # QA — solo en proyectos de tipo agent
```

Reglas clave del harness generado:

- **Tareas atómicas**: nada de "hazme el front" — el planner descompone todo
  objetivo amplio en tareas cortas con un único entregable verificable.
- **Modelo según complejidad**: cada tarea lleva `complejidad`; el leader la
  lanza con el tier correspondiente (alta → potente, media → intermedio,
  baja → económico).
- **Núcleo fijo de agentes**: leader, planner, implementer y reviewer están
  siempre; tester se suma solo en proyectos de tipo `agent`.

## Uso

```bash
pip install pydantic jinja2
python3 -m src.main
```

1. Elige modo: `[1] EJECUTOR` (autonomía) o `[2] PROFESOR` (te reta y pregunta).
2. Describe tu proyecto cubriendo las 7 dimensiones: tipo, stack, fuentes de
   datos, restricciones, criterios de done, entregable y tiempo disponible.
3. Si falta información, el intake te pide las dimensiones que faltan.
4. El harness aprobado queda en `harness/` — cópialo a la raíz de tu proyecto.

Para aplicarlo a un **proyecto ya empezado** (brownfield): genera el harness
aparte, fusiona `CLAUDE.md` a mano y ajusta `feature_list.json` al trabajo
que realmente queda. Soporte nativo pendiente para v2.

## Desarrollo

Metodología **SDD + TDD** estricta: actualizar spec → escribir test → implementar → commit.

- `SPEC.md` — spec general transversal + índice de specs por módulo
- `specs/<modulo>.md` — el contrato de cada módulo (trabaja solo con el tuyo)
- `errors/<modulo>.md` — errores conocidos por módulo; protocolo en `errors/ERRORS.md`
- `CLAUDE.md` — reglas generales y tabla de redirección por módulo

```bash
python3 -m pytest tests/ -q     # 37 tests
```

## Estado

v1 funcional: pipeline completo de extremo a extremo (intake → analysis →
generator → validator) con 37 tests en verde. Pendiente para v2: tool
`update_spec`, modo brownfield, clasificación por LLM en vez de keywords.

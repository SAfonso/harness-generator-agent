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

## Instalación

Dos vías, mismo código (`src/`), ver `specs/packaging.md`:

- **Pip**, para usarlo fuera de Claude Code:
  ```bash
  pip install -e .
  harness-agents
  ```
- **Skill de Claude Code**, para invocarlo con `/harness-agents` desde
  cualquier proyecto abierto en Claude Code: copia o enlaza
  `skill/harness-agents/` en tu carpeta de skills. Si el comando `harness-agents`
  no está ya instalado, la skill lo instala ella misma (`pip install -e
  <repo>`, que arrastra `pydantic`/`jinja2`) — nunca ejecuta el módulo en
  crudo, porque eso pondría el harness generado en el repo del generador en
  vez de en tu proyecto (ver `errors/packaging.md`).

## Uso

1. Elige modo: `[1] EJECUTOR` (autonomía) o `[2] PROFESOR` (te reta y pregunta).
2. Describe tu proyecto cubriendo las 7 dimensiones: tipo, stack, fuentes de
   datos, restricciones, criterios de done, entregable y tiempo disponible.
3. Si falta información, el intake te pide las dimensiones que faltan.
4. El harness aprobado se aplica **directamente en la raíz de tu proyecto**
   (`.claude/agents/`, `AGENTS.md`, `CHECKPOINTS.md`, `feature_list.json`,
   `init.sh`, `progress/`) — nada que copiar ni mover a mano. Se genera
   primero en aislado (`harness/`) para que el validator lo revise, y solo
   si aprueba se mueve a la raíz y se borra ese directorio temporal.

**Proyecto ya empezado (brownfield):** antes de preguntar, el pipeline
inspecciona el directorio destino (`inspect_project`, ver `specs/tools.md`) —
manifiestos de dependencias, historial git, `README.md`/`CLAUDE.md` existentes.
Si infiere el tipo de proyecto o el stack con evidencia clara, PROFESOR lo da
por bueno y solo confirma lo dudoso o pregunta lo que falte, en vez de repetir
la entrevista completa.

Además **audita** problemas mecánicos que romperían el harness generado (sin
repo/remoto git, sin CI, sin tests, documentación vacía, o un `CLAUDE.md`
existente) y, cuando hay código, recomienda pasar `/code-review`/`/security-review`
(eso sí requiere razonamiento, no lo hace `inspect_project`). Cada hallazgo
entra como tarea inicial en `feature_list.json` con su arreglo propuesto —
nunca se queda solo en comentario. El `README.md` del proyecto nunca se toca
ni se genera — es documentación de producto del usuario, no del harness.

**`CLAUDE.md` es el único fichero que se protege de una sobrescritura**: si
ya tienes uno, el generado se deja como `CLAUDE.harness.md` junto al tuyo en
vez de sustituirlo — fusionarlos sigue siendo manual (tarea en el backlog).
Todo lo demás se aplica sin preguntar, porque prácticamente nunca preexiste.

## Desarrollo

¿Te unes al proyecto por primera vez? `ONBOARDING.md` (English: `ONBOARDING.en.md`)
explica qué resuelve esto, cómo distinguir el generador (este repo) del harness que genera, y qué
hace cada agente, pensado para alguien que no ha visto el código nunca.

Metodología **SDD + TDD** estricta: actualizar spec → escribir test → implementar → commit.

- `SPEC.md` — spec general transversal + índice de specs por módulo
- `specs/<modulo>.md` — el contrato de cada módulo (trabaja solo con el tuyo)
- `errors/<modulo>.md` — errores conocidos por módulo; protocolo en `errors/ERRORS.md`
- `CLAUDE.md` — reglas generales y tabla de redirección por módulo

```bash
python3 -m pytest tests/ -q     # 109 tests
```

## Estado

v1 funcional: pipeline completo de extremo a extremo (intake → analysis →
generator → validator). v2 en marcha: empaquetado (pip + skill de Claude Code),
modo brownfield (`inspect_project` + confirmación en vez de entrevista desde
cero) y auditoría de salud del proyecto (git/CI/tests/docs → tareas del
backlog + recomendación de `/code-review`) ya implementados, 109 tests en verde.
Pendiente: tool `update_spec`, clasificación por LLM en vez de keywords,
inferir el resto de dimensiones (`data_sources`, `constraints`,
`acceptance_criteria`, `deliverable`, `time_available`) en brownfield cuando
haya evidencia explícita (`CHECKPOINTS.md`/`feature_list.json` de una
ejecución previa).

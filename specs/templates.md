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
│   └── ledger.json.j2    # v2 — ledger vacío ({"decisions": [], "tasks": []})
└── agents/               # Plantillas de agentes con modos
    ├── leader.md.j2      # modo: DIRECTOR
    ├── planner.md.j2     # modo: ARQUITECTO — tareas atómicas + complejidad
    ├── intake.md.j2      # modo: PROFESOR
    ├── analysis.md.j2    # modo: JUEZ
    ├── generator.md.j2   # modo: ESCRIBANO
    ├── implementer.md.j2 # modo: BISTURÍ
    ├── reviewer.md.j2    # modo: FISCAL
    ├── integrator.md.j2  # v2 — modo: NOTARIO, rama + commit/push/PR
    ├── watchman.md.j2    # v2 — modo: CENTINELA, CI + merge automático
    └── tester.md.j2      # modo: QA — solo proyectos de tipo agent
```

> El fichero de plantilla se llama por el **nombre interno del rol**
> (`role.name`, ej. `integrator`), igual que `implementer.md.j2` es BISTURÍ —
> `generator_agent` busca `agents/{role.name}.md.j2` sin caso especial
> (`src/agents/generator_agent.py`). El modo (NOTARIO, CENTINELA) solo aparece
> como contenido dentro del fichero, nunca en su nombre.

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
- Si `spec.audit_findings` no está vacío (brownfield), `feature_list.json.j2`
  añade una tarea por cada `AuditFinding`, con `id` continuando tras las 3
  tareas semilla fijas, `depends_on: [1]` (necesita el entorno inicializado) y:
  - `title`: `"Arreglar: {description} — {suggested_fix}"`
  - `severity="blocking"` → `priority="high"`, `complejidad="media"`
  - `severity="warning"` → `priority="medium"`, `complejidad="baja"`
  Ninguna de estas tareas necesita descomposición del planner — el
  `suggested_fix` ya es lo bastante concreto para ser una tarea atómica.

## v2 — NOTARIO, CENTINELA y ledger

- `integrator.md.j2` (modo NOTARIO) describe **dos** momentos, en secciones
  separadas dentro del mismo fichero: `## Al iniciar la tarea` (crea
  `task/{id}-{slug}` desde la rama por defecto del remoto, detectada, no
  hardcodeada) y `## Al cerrar la tarea` (commit + push de esa rama + abre/
  actualiza el PR, solo tras aprobación de FISCAL/QA)
- `watchman.md.j2` (modo CENTINELA) especifica que verifica CI y conflictos, y si están en verde
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

## v2 — disciplina de resolución de conflictos de merge

Integración por referencia de la skill externa `/resolving-merge-conflicts`
(aihero.dev) — mismo patrón que `code_quality_review_pending` en
`inspect_project` (`specs/tools.md`): se delega a una skill dedicada, nunca
se reimplementa su lógica dentro de las plantillas.

- `watchman.md.j2` (CENTINELA) distingue explícitamente, en el
  `failure_context` que entrega a FISCAL, un **conflicto de merge** de un
  **fallo de CI genérico** — nunca los mezcla — y recomienda invocar
  `/resolving-merge-conflicts` si está instalada.
- `reviewer.md.j2` (FISCAL) exige esa disciplina como condición del rechazo
  cuando el `failure_context` es un conflicto: la resolución debe rastrear la
  intención de cada lado (commit, PR o tarea de origen) y conservar ambos
  cambios donde sean compatibles — nunca acepta una resolución hecha con
  `--ours`/`--theirs` o borrando bloques sin más.
- `implementer.md.j2` (BISTURÍ) — quien de verdad toca el fichero en conflicto
  al reabrirse la tarea — documenta el mismo criterio como fallback manual si
  la skill no está instalada: rastrear intención, conservar lo compatible,
  documentar el trade-off si son incompatibles, y correr los checks del
  proyecto antes de dar el conflicto por resuelto — nunca deja el merge a
  medias.

## v2 — eje Standards vs eje Spec, y disciplina de repro en reintentos

Dos integraciones más por referencia (aihero.dev), mismo patrón que las
anteriores: delegar en una skill dedicada, no reimplementar su lógica.

- `reviewer.md.j2` (FISCAL) documenta explícitamente que cubre **solo el eje
  Spec** (¿cumple `CHECKPOINTS.md`?) — nunca evalúa convenciones de código,
  legibilidad o code smells, eso es el **eje Standards**, deliberadamente
  fuera de su alcance (ya lo era: "no rechaza por estilo o preferencia"). Antes
  de que NOTARIO cierre el PR, recomienda correr `/code-review` para cubrir
  ese eje — FISCAL no lo sustituye, ni lo bloquea si no está instalada.
- `implementer.md.j2` (BISTURÍ) — al reabrirse una tarea tras un rechazo de
  FISCAL, exige reproducir el motivo exacto del rechazo antes de tocar nada,
  y si es el 2º o 3er reintento (cerca del límite de 3 del leader), escribir
  2-3 hipótesis concretas de la causa antes de arreglar nada — nunca probar
  a ciegas. Recomienda `/diagnosing-bugs` si está instalada; si no, aplica el
  mismo criterio a mano: repro primero, hipótesis después, nunca al revés.

## v2 — mejoras tomadas de obra/superpowers

Evaluadas contra las plantillas reales (no adoptadas en bloque: el hook de
`SessionStart`, "rulings not stalls" y las skills que ya cubrimos con
`grill-me`/`tdd`/`diagnosing-bugs` quedaron fuera a propósito). Solo se
adopta lo que cubre un hueco verificado:

- **Evidencia antes de dar algo por hecho** (`verification-before-completion`):
  - `implementer.md.j2` (BISTURÍ): antes de entregar, corre los checks del
    proyecto (tests) y adjunta la salida fresca en su informe — nunca
    "debería pasar". Un bug corregido se verifica contra el síntoma original.
  - `reviewer.md.j2` (FISCAL): no se fía del informe de BISTURÍ — re-ejecuta
    los checks e inspecciona el diff real de la rama antes de aprobar.
  - `integrator.md.j2` (NOTARIO): solo commitea con esa evidencia fresca; sin
    evidencia no hay commit.
- **Escalada antes de molestar al humano** (`subagent-driven-development`):
  `leader.md.j2` (DIRECTOR) lanza el reintento tras el 2º rechazo en una
  sub-sesión nueva y con el tier de modelo inmediatamente superior antes de
  escalar al usuario en el 3º (`SPEC.md#flujo-de-ejecución-del-harness-generado`).
- **Tamaño mínimo de tarea** (`writing-plans`): `planner.md.j2` (ARQUITECTO)
  gana una cota inferior — cada tarea cuesta rama + PR + revisión + CI, así
  que no se sobre-divide: la unidad más pequeña que merece su propia revisión;
  el setup, la configuración y la documentación que solo sirven a una tarea se
  pliegan dentro de ella (una tarea de documentación propia solo si documentar
  es el entregable en sí). Sustituye la antigua regla "no mezcla documentar".
- **Guardas de NOTARIO/CENTINELA** (`using-git-worktrees`,
  `finishing-a-development-branch`): NOTARIO comprueba que el árbol de
  trabajo está limpio antes de crear la rama (`git status --porcelain`) y, si
  hay cambios ajenos a la tarea, para y avisa al leader — nunca hace stash,
  checkout forzado ni descarta nada por su cuenta. CENTINELA borra la rama
  `task/{id}-slug` (remota y local) tras un merge correcto. Los worktrees
  completos quedan fuera de alcance.
- **Restricciones y fuentes de datos llegan a los agentes** (hallazgo propio,
  inspirado en el "Global Constraints" de `writing-plans`): hasta ahora
  `spec.constraints` y `spec.data_sources` no las renderizaba ninguna
  plantilla, así que lo que el usuario contaba en la entrevista sobre ellas no
  llegaba a ningún agente. `CHECKPOINTS.md.j2`, `planner.md.j2`,
  `implementer.md.j2` y `reviewer.md.j2` renderizan `## Restricciones` (y las
  tres primeras también `## Fuentes de datos`), cada sección **solo si hay
  contenido** (sin cabeceras vacías). FISCAL rechaza una entrega que viole una
  restricción declarada.

## v2 — cabecera de subagente y entrada por el leader

Motivado por un error real (`errors/templates.md`): las plantillas de agente no
llevaban la cabecera YAML que Claude Code exige para registrar un fichero de
`.claude/agents/` como subagente, así que los agentes generados existían pero
nunca se podían invocar.

- **Cabecera obligatoria.** Todo fichero `agents/*.md.j2` que se genera dentro
  del harness empieza con un bloque frontmatter con exactamente dos campos:
  - `name`: `{{ agent.name }}` (el nombre interno del rol, p. ej. `implementer`)
  - `description`: `{{ agent.scope }}` — el `scope` del `AgentRole`, que ya
    describe cuándo usar al agente. Nunca vacío.
- **Sin `model`.** La cabecera nunca fija un modelo: el leader lo decide por
  tarea según su `complejidad` (alta → potente, media → intermedio, baja →
  económico). Un modelo por defecto en el fichero pisaría esa decisión.
- **Sin `tools`.** No se añade: los subagentes heredan las del proyecto. Si
  `AgentRole.tools` llegara a usarse, es una tarea aparte.
- **Todo pasa por el leader.** `CLAUDE.md.j2` incluye una sección
  `## Cómo trabajar` que ordena delegar en el leader **cualquier instrucción
  nueva del usuario** que implique cambiar el proyecto (no las preguntas
  puramente informativas), en ambos modos (EJECUTOR y PROFESOR).
- **El leader entrevista antes de planificar.** `leader.md.j2` añade la
  sección `## Instrucción nueva del usuario`: antes de crear tareas, hace las
  preguntas al estilo PROFESOR (comportamiento esperado, casos límite,
  restricciones; sin aceptar vaguedad ni rellenar huecos por su cuenta),
  escribe o actualiza la spec donde el proyecto ya tenga esa convención, y solo
  entonces pasa el objetivo al planner para que lo descomponga en tareas
  atómicas con complejidad. Nunca asigna una tarea sin spec detrás.

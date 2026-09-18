# ONBOARDING — harness-generator-agent

> 🇬🇧 English version: [`ONBOARDING.en.md`](ONBOARDING.en.md)

> Esto es un tour guiado del proyecto, pensado para alguien que se une hoy y
> no ha visto el código nunca. No sustituye a los specs (`SPEC.md`,
> `specs/*.md`) — cuando vayas a tocar código, esos son el contrato real y
> tienen prioridad sobre este documento. Este fichero es el mapa; los specs
> son el territorio.

---

## TL;DR (30 segundos)

Este proyecto **no es una app** que uses tú directamente en tu día a día.
Es una **fábrica de configuraciones para Claude Code**: le describes un
proyecto (o le apuntas a uno que ya existe) y te devuelve una carpeta
(`harness/`) con reglas, agentes con personalidad propia y un backlog de
tareas — todo pensado para que trabajar con Claude Code en ese proyecto sea
disciplinado, verificable y no se descontrole.

Hay **dos sistemas completamente distintos** en este repo y es fácil
confundirlos:

```
SISTEMA A — "El Generador"                SISTEMA B — "El Harness Generado"
(este repo, se ejecuta UNA VEZ)           (vive DENTRO de tu proyecto,
                                            se ejecuta CONTINUAMENTE)

  tu descripción / tu proyecto               DIRECTOR (leader)
         │                                        │
         ▼                                   ARQUITECTO (planner)
  intake_agent (PROFESOR)                         │
         │                                   BISTURÍ (implementer)
         ▼                                        │
  analysis_agent (JUEZ)                      FISCAL (reviewer) ──► QA (tester)
         │                                        │
         ▼                                   NOTARIO (integrator)
  generator_agent (ESCRIBANO)                     │
         │                                   CENTINELA (watchman)
         ▼
  validator_agent (FISCAL)
         │
         ▼
     harness/  ────────────────────────►  esto es lo que instalas en tu
                                            proyecto y se convierte en
                                            Sistema B
```

Si en algún momento lees "FISCAL" y no sabes si se refiere al Sistema A o al
B: hay una sección más abajo (§5) dedicada exactamente a esa trampa.

---

## 1. El problema que resuelve

Cuando alguien usa Claude Code (o cualquier LLM agente) para construir un
proyecto sin estructura, aparecen siempre los mismos problemas:

- El agente intenta abarcar objetivos enormes ("hazme el backend completo")
  en vez de tareas pequeñas y verificables.
- No hay disciplina de tests: se implementa y ya, sin verificar antes/después.
- El trabajo aprobado se pierde porque nadie hizo commit (pasó de verdad: un
  `git reset` externo revirtió tareas ya aprobadas en uno de los proyectos
  donde se aplicó este harness antes de que existiera NOTARIO — motivo real
  detrás de por qué NOTARIO commitea al cerrar cada tarea, ver `specs/generator_agent.md#v2`).
- Cada sesión reinventa las reglas del proyecto porque no hay un sitio fijo
  donde estén escritas.
- Si el proyecto ya existe (no es un "folio en blanco"), no hay manera de
  que el agente entienda rápido qué hay y qué falta.

Este generador ataca eso produciendo un **harness**: una carpeta con reglas
explícitas, un backlog de tareas atómicas con complejidad asignada, y varios
"agentes" (perfiles de comportamiento, no procesos separados) que se turnan
el trabajo con responsabilidades muy concretas.

---

## 2. Glosario rápido (antes de seguir)

| Término | Qué significa aquí |
|---|---|
| **Harness** | La carpeta (`harness/`) que este repo genera: `CLAUDE.md`, `AGENTS.md`, `CHECKPOINTS.md`, `feature_list.json`, `.claude/agents/*.md`, etc. Es lo que se instala en tu proyecto. |
| **Agente** | No es un proceso ni un microservicio — es un **fichero Markdown** (`.claude/agents/nombre.md`) con instrucciones de comportamiento que Claude Code lee y adopta como personalidad al trabajar en ese rol. |
| **Modo** | El "nombre en clave" de un agente (DIRECTOR, FISCAL, PROFESOR...). Es cosmético mnemotécnico, pero cada modo tiene reglas de comportamiento muy concretas detrás — no es solo un nombre bonito. |
| **`HarnessSpec`** | La estructura de datos (Pydantic) que viaja por el Sistema A. Cada agente del generador la lee y/o la completa. Está definida en `specs/models.md` / `src/models/harness_spec.py`. |
| **Backlog atómico** | `feature_list.json`: lista de tareas cortas, cada una con **un único entregable verificable** — nunca "hazme el front entero". |
| **SDD** | Spec-Driven Development: nada se programa sin que esté descrito antes en un `spec`. El spec es el contrato. |
| **TDD** | Test-Driven Development: el test se escribe antes que la implementación, y se ve fallar (rojo) antes de hacerlo pasar (verde). |
| **Brownfield / Greenfield** | Greenfield = proyecto desde cero. Brownfield = proyecto que ya existe y tiene código/historial que hay que respetar. Este generador soporta ambos (ver §4.5). |

---

## 3. Sistema A en detalle — el generador (este repo)

Este es el pipeline que se ejecuta **una sola vez** para producir tu
`harness/`. Está escrito en Python puro (Pydantic + Jinja2), sin LLM real
dentro del código — los "agentes" de este sistema son funciones deterministas
(heurísticas de keywords) que **simulan** lo que un LLM haría, para que todo
el pipeline sea testeable con `pytest` sin gastar tokens ni depender de red.

```
run_pipeline(text, mode, output_dir)          ←  src/main.py
   │
   ├─► inspect_project(output_dir)             ←  brownfield, ver §4.5
   │
   ├─► run_intake(text, mode, inspection)       ←  intake_agent.py  (PROFESOR)
   │        │
   │        ├─ status="needs_input" → se corta aquí, no se genera nada
   │        └─ status="complete" → HarnessSpec parcial
   │
   ├─► run_analysis(spec)                       ←  analysis_agent.py (JUEZ)
   │        → HarnessSpec completa (agentes, complejidad, reglas)
   │
   ├─► run_generator(spec, harness/)            ←  generator_agent.py (ESCRIBANO)
   │        → escribe todos los ficheros del harness
   │
   └─► run_validator(harness/, spec)            ←  validator_agent.py (FISCAL)
            → veredicto: aprobado / rechazado (8 checks)
```

### 3.1 ¿Qué es "intake"?

**Intake es literalmente "recogida de información"** — es el primer y único
agente de este sistema que tiene "contacto" con el usuario (o con el
proyecto existente, en brownfield). Su trabajo es rellenar 7 dimensiones
sobre lo que se quiere construir:

1. `project_type` — tipo de proyecto (`data_pipeline`, `api`, `web`, `agent`, `cli`, `other`)
2. `stack` — tecnologías principales
3. `data_sources` — de dónde vienen los datos/inputs
4. `constraints` — limitaciones conocidas (sin red, rate limits...)
5. `acceptance_criteria` — qué significa "terminado"
6. `deliverable` — qué se entrega al final
7. `time_available` — cuánto tiempo hay

Si el texto que describe el proyecto ya cubre las 7 (input "rico"), intake
las extrae todas de golpe. Si falta información (input "escaso"), devuelve
`status="needs_input"` con la lista de lo que falta — y **no se genera nada**
hasta que se completa. Esa es la diferencia clave con simplemente "programar
un formulario": intake no avanza con huecos.

Su modo es **PROFESOR**: no acepta respuestas vagas, y si algo no tiene
sentido (un stack raro para el tipo de proyecto, un plazo poco realista, un
criterio de aceptación subjetivo) lo dice con un argumento concreto en vez de
validarlo por defecto.

📄 Spec: `specs/intake_agent.md` · Código: `src/agents/intake_agent.py`

### 3.2 Los 4 agentes del Sistema A, uno por uno

| Agente | Modo | Qué hace | Entrada → Salida |
|---|---|---|---|
| **`intake_agent`** | PROFESOR | Entrevista (o confirma, en brownfield) hasta cubrir las 7 dimensiones | texto libre → `HarnessSpec` parcial |
| **`analysis_agent`** | JUEZ | Decide la estructura: confirma el tipo de proyecto, calcula la complejidad del harness según el tiempo disponible, arma la lista de agentes (`AgentRole`) que tendrá el harness generado, y las reglas específicas | `HarnessSpec` parcial → `HarnessSpec` completa |
| **`generator_agent`** | ESCRIBANO | Renderiza cada fichero del harness a partir de plantillas Jinja2, en un orden fijo (para que cada fichero pueda referenciar a los anteriores sin contradicciones) | `HarnessSpec` completa → ficheros en `harness/` |
| **`validator_agent`** | FISCAL | Pasa 8 checks automáticos sobre lo generado (¿coinciden los agentes de `AGENTS.md` con los ficheros reales? ¿hay tareas pendientes? ¿algún `{{` sin resolver?...) y emite veredicto | `harness/` + `HarnessSpec` → aprobado/rechazado + informe |

Cada uno tiene su propio spec (`specs/<agente>.md`) y su propio fichero de
errores conocidos (`errors/<agente>.md`) — no hace falta leer los de un
agente que no vas a tocar.

### 3.3 `HarnessSpec` — el estado compartido

Es la única estructura que viaja por todo el pipeline. Piénsalo como una
ficha que se va rellenando: `intake_agent` escribe la mitad de los campos,
`analysis_agent` rellena el resto (`agent_roles`, `harness_complexity`,
`rules`), y `generator_agent`/`validator_agent` solo la leen. Está definida
en `src/models/harness_spec.py` (contrato en `specs/models.md`).

### 3.4 Brownfield: cuando el proyecto ya existe

Si `output_dir` (donde se va a generar el harness) ya tiene señales de ser un
proyecto real —manifiestos (`requirements.txt`, `package.json`...), historial
de git, un `README.md`/`CLAUDE.md` con contenido—, antes de preguntar nada
`run_pipeline` llama a `inspect_project()`:

- **Infiere** lo que puede (tipo de proyecto y stack) con evidencia concreta
  y un nivel de confianza (`high`/`low`). Si es `high`, PROFESOR no vuelve a
  preguntarlo — lo confirma en el mensaje de apertura. Si es `low`, sí pide
  confirmación puntual (nunca asume en silencio).
- **Audita** problemas mecánicos que romperían el harness generado: sin
  repositorio o remoto git (NOTARIO no podría hacer commit/PR), sin CI
  (CENTINELA no tendría nada que verificar), sin tests, documentación vacía,
  o un `CLAUDE.md` ya existente que habrá que fusionar a mano. Cada hallazgo
  se convierte en una **tarea inicial del backlog generado** — nunca se
  queda solo como comentario.
- Nunca toca ni genera el `README.md` del proyecto — eso es documentación de
  producto del usuario, fuera del alcance del harness.

📄 Spec: `specs/tools.md#inspect_project` · Código: `src/tools/inspect_project.py`

---

## 4. Sistema B en detalle — el harness que se instala en tu proyecto

Esto es lo que realmente vas a usar día a día una vez generado. Vive dentro
de **tu** proyecto (no de este repo) y lo ejecuta Claude Code directamente
—no hay ningún motor Python orquestándolo, los ficheros `.claude/agents/*.md`
son instrucciones que Claude Code sigue al pie de la letra. Esto es la raíz
de tu proyecto **tras** la aplicación automática (§6) — no una subcarpeta
`harness/` que tengas que mover tú:

```
tu-proyecto/  (la raíz — no una subcarpeta)
├── CLAUDE.md              # lo primero que lee Claude Code: modo, reglas, política de modelos
├── AGENTS.md              # mapa de todos los roles y sus modos
├── CHECKPOINTS.md         # criterios de aceptación (contra esto revisa FISCAL)
├── feature_list.json      # backlog: tareas atómicas + complejidad (alta|media|baja)
├── init.sh                # verifica que el entorno (git, gh, etc.) está listo
├── progress/
│   └── ledger.json        # memoria persistente de DIRECTOR entre tareas (decisiones + resúmenes)
└── .claude/agents/
    ├── leader.md          # DIRECTOR
    ├── planner.md         # ARQUITECTO
    ├── implementer.md     # BISTURÍ
    ├── reviewer.md        # FISCAL
    ├── integrator.md      # NOTARIO
    ├── watchman.md        # CENTINELA
    └── tester.md          # QA (solo si el proyecto es de tipo "agent")
```

### 4.1 El núcleo fijo de agentes, uno por uno

Este conjunto **no cambia según el tipo de proyecto** — es siempre el mismo
(salvo `tester`, que solo aparece en proyectos tipo `agent`). No se inventan
agentes nuevos por capricho.

| Agente | Modo | Su trabajo, en una frase |
|---|---|---|
| **`leader`** | **DIRECTOR** | Orquesta la ejecución tarea a tarea. No opina sobre diseño, coordina. Escala al usuario si algo se rechaza 3 veces. Su memoria entre tareas es `progress/ledger.json`, no una conversación larga — así cada tarea arranca con una sub-sesión limpia y un paquete de contexto mínimo, no con el historial completo. |
| **`planner`** | **ARQUITECTO** | Descompone objetivos amplios en tareas atómicas y les asigna complejidad (`alta`\|`media`\|`baja`) — esa complejidad decide qué nivel de modelo LLM se usa para esa tarea. |
| **`implementer`** | **BISTURÍ** | Implementa **una** tarea, sin salirse del scope que le han dado. No decide arquitectura, no toca lo que no le han pedido. |
| **`reviewer`** | **FISCAL** | Aprueba o rechaza el trabajo de BISTURÍ contrastándolo contra `CHECKPOINTS.md`. No busca bugs por iniciativa propia — contrasta contra lo pactado. *(Ojo: hay OTRO "FISCAL" en el Sistema A — ver §6.)* |
| **`integrator`** | **NOTARIO** | Formaliza en git lo ya aprobado: crea la rama `task/{id}-slug` al empezar la tarea, y hace commit + push + PR al cerrarla, solo tras la aprobación de FISCAL (o QA). |
| **`watchman`** | **CENTINELA** | Verifica CI y conflictos del PR. Si está todo en verde, **mergea automáticamente** — no espera aprobación humana (funciona en modo desatendido). Si falla, reabre el ciclo con FISCAL en vez de relanzar BISTURÍ a ciegas. |
| **`tester`** | **QA** | Solo en proyectos tipo `agent`. Diseña y ejecuta tests de comportamiento antes de que FISCAL apruebe. |

### 4.2 El ciclo de vida de una tarea

Por cada tarea `pending` de `feature_list.json`, este es el recorrido real:

```
NOTARIO (crea rama task/{id}-slug)
   │
   ▼
BISTURÍ (implementa, scope estricto)
   │
   ▼
FISCAL (revisa) ──rechazo──► vuelve a BISTURÍ (máx. 3 rechazos, luego escala a DIRECTOR)
   │
   aprobado (+ QA si aplica)
   ▼
NOTARIO (commit + push + PR)
   │
   ▼
CENTINELA (CI + merge)
   │
   ├─ verde → merge automático, tarea cerrada
   └─ falla → reabre el ciclo con FISCAL, con el contexto del fallo adjunto
```

Al cerrar la tarea (integrada o escalada), se añade un resumen destilado a
`progress/ledger.json` — nunca el log crudo de la conversación.

**Si el fallo de CENTINELA es un conflicto de merge** (no CI en rojo), se
trata distinto de un fallo de CI genérico: CENTINELA lo marca explícitamente
como tal, FISCAL exige que la resolución rastree la intención de cada lado
(commit, PR o tarea de origen) en vez de aceptar `--ours`/`--theirs` a lo
bruto, y BISTURÍ —quien de verdad toca el fichero al reabrirse la tarea—
aplica ese criterio (o usa la skill `/resolving-merge-conflicts` si está
instalada). Integración por referencia, mismo patrón que la recomendación de
`/code-review` en `inspect_project` (§3.4): delegar a una skill dedicada, no
reinventarla.

**FISCAL cubre deliberadamente solo el "eje Spec"** (¿cumple
`CHECKPOINTS.md`?) — nunca convenciones de código ni code smells, eso es el
"eje Standards", fuera de su alcance por diseño. Antes de que NOTARIO cierre
el PR, recomienda correr `/code-review` para ese eje. Y **si una tarea se
reabre tras un rechazo**, BISTURÍ no prueba a ciegas: reproduce el motivo
exacto del rechazo antes de tocar nada, y a partir del 2º reintento escribe
hipótesis concretas antes de arreglar — usa `/diagnosing-bugs` si está
instalada, o el mismo criterio a mano si no. Dos integraciones más por
referencia, mismo patrón.

### 4.3 Los ficheros clave que vas a mirar como junior

- **`CLAUDE.md`** — léelo siempre primero al entrar a un proyecto con este
  harness instalado. Dice el modo activo y las reglas no negociables.
- **`feature_list.json`** — el backlog. Aquí ves qué está pendiente, en
  curso o hecho, y con qué complejidad.
- **`CHECKPOINTS.md`** — si quieres saber "¿esto se considera terminado?",
  la respuesta está aquí, no en tu criterio personal.
- **`progress/ledger.json`** — el historial de decisiones importantes,
  para no tener que releer toda la conversación.

---

## 5. La trampa del nombre repetido: FISCAL ≠ FISCAL

Vas a ver "FISCAL" en dos sitios distintos y **no es el mismo agente**:

| | Sistema A (este repo) | Sistema B (harness generado) |
|---|---|---|
| Agente | `validator_agent` | `reviewer` |
| Cuándo actúa | Una vez, al final de la generación del harness | Continuamente, en cada tarea del backlog |
| Contra qué valida | Los 8 checks de coherencia del harness generado | `CHECKPOINTS.md` de tu proyecto |
| Fichero | `src/agents/validator_agent.py` | `.claude/agents/reviewer.md` (generado) |

Ambos comparten filosofía ("no busca bugs, contrasta contra lo pactado") y
por eso alguien les puso el mismo nombre en clave — pero son agentes
distintos, en sistemas distintos, que nunca se ejecutan en la misma fase.
Si lees "FISCAL" en una conversación, pregunta (o mira el contexto) de cuál
de los dos se está hablando.

---

## 6. Cómo se instala y se usa (resumen)

Detalle completo en `README.md`; aquí solo el mapa mental:

1. **Instalar el generador** (una vez): `pip install -e .` deja disponible
   el comando `harness-agents`. También existe una skill de Claude Code
   (`skill/harness-agents/`) que instala esto por ti la primera vez que la
   invocas con `/harness-agents`.
2. **Ejecutarlo dentro de tu proyecto** (greenfield o brownfield, da igual):
   `cd tu-proyecto && harness-agents`. Importa mucho el `cwd` — el harness
   se genera siempre en el directorio desde el que arrancas, nunca en el
   repo de este generador (hubo un bug real por esto, documentado en
   `errors/packaging.md` — vale la pena leerlo, es un buen ejemplo de cómo
   funciona el protocolo de errores del repo).
3. Eliges modo (`EJECUTOR` o `PROFESOR`), describes el proyecto (o dejas que
   la inspección brownfield rellene lo que pueda), y si se aprueba, el
   harness se aplica **directamente en la raíz de tu proyecto** — nada que
   mover ni copiar a mano. Por dentro se genera primero en `harness/`
   (aislado, para que el validator lo revise) y `apply_harness()` lo mueve a
   la raíz y borra ese directorio temporal solo si se aprueba
   (`specs/tools.md#apply_harness`) — si se rechaza, se queda en `harness/`
   sin aplicar, para poder inspeccionar el informe.
4. Solo `CLAUDE.md` se protege de una sobrescritura: si ya tenías uno, el
   generado queda como `CLAUDE.harness.md` junto al tuyo — fusionarlos sigue
   siendo manual (hay una tarea para ello en el backlog, `existing_claude_md`).
   Todo lo demás (`.claude/agents/`, `AGENTS.md`, `CHECKPOINTS.md`,
   `feature_list.json`, `init.sh`, `progress/`) se aplica sin preguntar,
   porque prácticamente nunca preexiste.

**Si lo invocas desde dentro de Claude Code** (vía `/harness-agents`, no
tecleando tú mismo en una terminal), `harness-agents` a secas **no
funciona**: usa `input()`, y el tool de Bash de un agente no sostiene una
conversación de stdin turno a turno — revienta con `EOFError` en el primer
prompt (otro bug real, esta vez encontrado en producción sobre un proyecto
real, `errors/main.md`). Por eso `main()` acepta `--text`: la skill hace que
Claude pregunte en el propio chat, arme `harness-agents --text "..." --mode
... --output-dir "$(pwd)"`, y si la salida pide más información, vuelva a
invocar con el texto ampliado — Claude es la capa conversacional, nunca el
subproceso.

---

## 7. Cómo está organizado este repo (si vas a tocar código)

La regla de oro, sin excepciones, está en `CLAUDE.md` y `SPEC.md`:

> **SDD + TDD estricto:** actualizar el spec del módulo → escribir el test
> (verlo fallar) → implementar → verlo pasar → commit.

No se programa nada que no esté descrito antes en `specs/<módulo>.md`. Si te
piden una función nueva y no está en el spec, el primer paso es **editar el
spec**, no escribir código.

| Si vas a tocar… | Lee su spec | Y sus errores conocidos |
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

**Protocolo de errores** (en `errors/ERRORS.md`): si te encuentras un error,
primero busca si ya está documentado en `errors/<módulo>.md` — si lo está,
aplica la solución ya escrita, no reinvestigues desde cero. Si es nuevo,
resuélvelo y regístralo antes de dar la tarea por cerrada. El objetivo:
ningún error se investiga dos veces.

**Tests:** `python3 -m pytest tests/ -q` antes de cada commit. Usa el
fixture `tmp_path` de pytest para todo lo que toque el filesystem —
nunca crees ficheros de prueba a mano en el repo. Dos reglas de calidad
explícitas en `SPEC.md`: `monkeypatch`/mocks solo en fronteras externas
reales (filesystem, rutas/config), nunca para simular la lógica de otra
función propia; y ningún test tautológico (el valor esperado tiene que ser
un literal trazable al spec, no el resultado de recalcular con la misma
fórmula que el código bajo test).

---

## 8. Cosas raras que vas a encontrar (honestidad, no vergüenza)

Un proyecto real tiene deuda técnica documentada, no escondida:

- **`src/templates/agents/intake.md.j2`, `analysis.md.j2`, `generator.md.j2`
  existen pero no se usan.** El núcleo real de agentes generados
  (`_CORE_AGENTS` en `src/config.py`) es `leader, planner, implementer,
  reviewer, integrator, watchman` (+`tester`) — nunca incluye `intake`,
  `analysis` ni `generator` como agentes del harness generado. Esas tres
  plantillas son de una iteración de diseño anterior. No hacen daño (nunca
  se renderizan), pero si las editas pensando que hacen algo, no.
- **`PROJECT.md` está desactualizado** en su tabla de "Modos por agente" y en
  el árbol de `harness/` que describe — mezcla agentes del Sistema A con los
  del Sistema B como si fueran el mismo conjunto. `README.md` y
  `SPEC.md` reflejan el estado real; en caso de duda, confía en esos dos.
- **En brownfield, solo se infieren 2 de las 7 dimensiones** (`project_type`
  y `stack`). Las otras 5 (`data_sources`, `constraints`,
  `acceptance_criteria`, `deliverable`, `time_available`) solo se rellenarían
  si hubiera evidencia explícita de una ejecución previa del harness
  (`CHECKPOINTS.md`/`feature_list.json` ya existentes) — y eso todavía no
  está implementado.
- **`progress/current.md`, `history.md`, `errors.md`** aparecen mencionados
  en reglas/specs antiguos como parte de lo que debería generarse, pero hoy
  solo `progress/ledger.json` se genera de verdad.
- **Ejecutar el generador dos veces sobre el mismo proyecto sobrescribe sin
  avisar** `feature_list.json`, `progress/ledger.json` y `.claude/agents/*.md`
  — `apply_harness()` (`specs/tools.md`) solo protege `CLAUDE.md` de una
  sobrescritura. Re-ejecuciones idempotentes sobre un proyecto que ya tiene
  el harness aplicado no están resueltas.

Si buscas una primera tarea para aprender el flujo SDD+TDD del repo sin
riesgo, limpiar cualquiera de estos puntos (spec → test → implementación →
commit) es un buen candidato.

---

## 9. Por dónde seguir

1. Lee `SPEC.md` entero una vez — es corto y es el contrato transversal.
2. Corre la suite: `python3 -m pytest tests/ -q` (debería estar en verde).
3. Genera un harness de prueba sobre un directorio vacío para ver el flujo
   greenfield completo, y luego sobre uno con un `requirements.txt` para ver
   el flujo brownfield + la auditoría en acción.
4. Cuando vayas a tocar un módulo concreto, ve directo a su fila en la tabla
   de §7 — no hace falta leer los specs de los módulos que no tocas.
5. Si algo de este documento no cuadra con lo que ves en el código, el
   código (y su spec) gana siempre — actualiza este `ONBOARDING.md` de paso.

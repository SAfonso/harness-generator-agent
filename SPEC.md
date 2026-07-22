# SPEC.md — harness-generator-agent (spec general)

Este fichero contiene **solo lo transversal**: objetivo, metodología, arquitectura,
modos y criterios de aceptación. El detalle de cada módulo vive en `specs/<modulo>.md` —
trabaja con el spec de tu módulo sin necesidad de leer los demás.

## Objetivo

Dado un input del usuario describiendo su proyecto, producir un directorio `harness/`
completamente personalizado y listo para usar con Claude Code.

---

## Índice de specs por módulo

| Módulo | Spec | Errores conocidos | Código | Tests |
|---|---|---|---|---|
| Modelos de datos | `specs/models.md` | `errors/models.md` | `src/models/harness_spec.py` | indirectos |
| Tools | `specs/tools.md` | `errors/tools.md` | `src/tools/` | `tests/test_assess_input.py`, `tests/test_classify_project.py`, `tests/test_render_template.py`, `tests/test_validate_harness.py` |
| intake_agent (PROFESOR) | `specs/intake_agent.md` | `errors/intake_agent.md` | `src/agents/intake_agent.py` | `tests/test_intake_agent.py` |
| analysis_agent (JUEZ) | `specs/analysis_agent.md` | `errors/analysis_agent.md` | `src/agents/analysis_agent.py` | `tests/test_analysis_agent.py` |
| generator_agent (ESCRIBANO) | `specs/generator_agent.md` | `errors/generator_agent.md` | `src/agents/generator_agent.py` | `tests/test_generator_agent.py` |
| validator_agent (FISCAL) | `specs/validator_agent.md` | `errors/validator_agent.md` | `src/agents/validator_agent.py` | `tests/test_validator_agent.py` |
| Plantillas | `specs/templates.md` | `errors/templates.md` | `src/templates/` | vía render_template |
| Entrypoint | `specs/main.md` | `errors/main.md` | `src/main.py` | `tests/test_main.py` |

Errores transversales (≥ 2 módulos o entorno): `errors/ERRORS.md`, que además
define el protocolo de gestión de errores.

---

## Metodología

- **SDD:** los specs SON el contrato. Nada se implementa sin estar definido primero
  en el spec de su módulo. Si necesitas algo que no está, actualiza el spec **antes**
  de escribir código. Lo transversal se actualiza aquí; lo del módulo, en su spec.
- **TDD:** cada función, tool y agente tiene sus tests escritos antes de su implementación.
- **Orden obligatorio en cada tarea:** actualizar spec del módulo → escribir test → implementar → commit.

---

## Arquitectura general

```
src/
├── agents/
│   ├── intake_agent.py       # PROFESOR — entrevista al usuario
│   ├── analysis_agent.py     # JUEZ — decide estructura del harness
│   ├── generator_agent.py    # ESCRIBANO — genera ficheros
│   └── validator_agent.py    # FISCAL — valida coherencia final
├── tools/                    # Funciones puras que usan los agentes
├── templates/                # Plantillas Jinja2 (base/ + agents/)
├── models/
│   └── harness_spec.py       # Estado compartido entre agentes
├── main.py                   # Entrypoint — elige modo y lanza el flujo
└── config.py                 # Constantes, tipos de proyecto, modos
```

**Pipeline:** `intake → analysis → generator → validator`, con `HarnessSpec`
como estado compartido que viaja por los cuatro agentes.

---

## Modos por agente (transversal — aplica a todos los harnesses generados)

| Agente | Modo | Razón |
|---|---|---|
| leader | DIRECTOR | Orquesta la ejecución, no decide sobre diseño — coordina sin entrar en el contenido |
| planner | ARQUITECTO | Descompone objetivos en tareas atómicas y les asigna complejidad — diseña el plan, no lo ejecuta |
| intake | PROFESOR | Único agente en contacto con el usuario en fase de diseño |
| analysis | JUEZ | Decide sin ruido, justifica en una línea |
| generator | ESCRIBANO | Coherencia entre ficheros por encima de todo |
| implementer | BISTURÍ | Scope estricto, mínimo viable verificable |
| reviewer | FISCAL | Contrasta contra contrato, no busca bugs |
| integrator | NOTARIO | Formaliza en git lo ya aprobado — rama al iniciar, commit+push+PR al cerrar |
| watchman | CENTINELA | Verifica CI/merge y mergea en automático si está en verde; si falla, reabre el ciclo con FISCAL |
| tester | QA | Solo para proyectos de tipo agent — verifica comportamiento antes de aprobar |

Los modos son fijos y viven en `src/config.py` (`AGENT_MODES`). Las reglas de
comportamiento de cada modo están en el spec del agente correspondiente.

---

## Flujo de ejecución del harness generado (runtime, v2)

A diferencia del flujo de construcción de este repo (arriba), esto describe cómo
se ejecuta el harness **ya generado**, tarea a tarea, sobre `feature_list.json` en
el proyecto destino. Es comportamiento especificado en `leader.md.j2` y los
ficheros de agente — no hay motor Python que lo orqueste, lo ejecuta Claude Code.
La especificación de este flujo está completa y verificada por tests
(`tests/test_generator_agent.py`, `tests/test_validate_harness.py`): lo que NO
existe es un motor Python que lo ejecute, porque no lo necesita — el propio
Claude Code, siguiendo estos ficheros, es quien lo ejecuta.

**Estado persistente de DIRECTOR:** deja de mantener memoria conversacional larga
entre tareas. Su estado vive en `progress/ledger.json` (modelo `Ledger` —
`specs/models.md`): decisiones (`LedgerDecision`) y resúmenes de tareas cerradas
(`TaskCloseOut`).

**Sesión aislada por tarea:** por cada tarea `pending` de `feature_list.json`,
DIRECTOR:

1. Construye un `ContextPackage` (tarea + decisiones del ledger relevantes por
   `scope`/`depends_on` + resúmenes de las tareas de las que depende + criterios
   de aceptación relevantes de `CHECKPOINTS.md`) — nunca pasa el ledger completo
   ni el historial de conversación.
2. Lanza una sub-sesión (subagente) con ese paquete, con el modelo según la
   `complejidad` de la tarea (comportamiento ya existente en el leader).
3. La sub-sesión ejecuta: `NOTARIO(rama) → BISTURÍ → FISCAL(→QA) → NOTARIO(commit+push+PR) → CENTINELA(CI+merge)`.
   - NOTARIO crea `task/{id}-{slug}` desde la rama por defecto del remoto al
     iniciar la tarea, y hace commit+push+PR al cerrarla, solo tras aprobación
     de FISCAL(+QA).
   - CENTINELA verifica CI y conflictos; si están en verde hace merge automático
     del PR — el batch corre desatendido, no espera aprobación humana.
   - Un rechazo de FISCAL o un fallo de CENTINELA cuentan igual contra el límite
     de 3 rechazos ya existente en el leader; un fallo de CENTINELA reabre el
     ciclo devolviendo el control a FISCAL con el `failure_context` de
     `IntegrationReport` adjunto — nunca relanza BISTURÍ a ciegas ni repite la
     tarea desde cero.
4. Al cerrar (integrada o escalada), la sub-sesión devuelve un `TaskCloseOut` a
   DIRECTOR, que lo añade a `progress/ledger.json` (resumen destilado, nunca el
   log crudo) y actualiza el `status` de la tarea en `feature_list.json`.

---

## Testing (convenciones transversales)

- Framework: **pytest**
- Los tests viven en `tests/` con el prefijo `test_` (ej: `tests/test_classify_project.py`)
- Cada tool en `src/tools/` tiene su fichero de tests **antes** de implementar los agentes
- Cada agente en `src/agents/` tiene su fichero de tests **antes** de implementar `main.py`
- Convenio **TDD**: test primero, implementación después — sin excepciones
- Para probar funciones que tocan el filesystem usar el fixture `tmp_path` de pytest
  (no crear ficheros en el repo ni en `/tmp` a mano)
- Para sobreescribir variables a nivel de módulo (ej: `TEMPLATES_DIR`) usar `monkeypatch`
  de pytest en lugar de modificar la función original

---

## Criterios de aceptación del proyecto

1. Dado un input de tipo `data_pipeline`, el harness generado es distinto
   al generado para un input de tipo `api`
2. En modo PROFESOR, el intake_agent reta al menos una decisión del usuario
3. El validator_agent rechaza un harness con placeholders sin resolver
4. El flujo completo termina en menos de 2 minutos para un input rico
5. El harness generado puede usarse directamente en Claude Code sin modificaciones

---

## Lo que NO estaba en v1 (bloque original del hackathon)

- Memoria entre sesiones
- Soporte para más de 4 agentes en el harness generado
- Integración con git (commit/push/PR/merge) y verificación de CI
- Personalización de plantillas por el usuario
- Interfaz web
- `update_spec` operativo (definido en `specs/tools.md`, implementación pendiente)

## v2 — añadido (memoria entre sesiones + integración git)

Implementado y con tests en verde (commits `ef27508`..`29c4b01`):

| Pieza | Spec | Código/tests |
|---|---|---|
| Agentes NOTARIO (`integrator`) y CENTINELA (`watchman`) — núcleo fijo, 6 agentes | `specs/templates.md`, tabla de modos arriba | `src/templates/agents/integrator.md.j2`, `watchman.md.j2`; `config.py#_CORE_AGENTS` |
| Ledger (`progress/ledger.json`) + `ContextPackage` + `TaskCloseOut` + `IntegrationReport` + `LedgerDecision` | `specs/models.md` | `src/models/harness_spec.py`, `tests/test_models.py` |
| `progress/ledger.json` generado vacío como 4º fichero base | `specs/generator_agent.md` | `src/agents/generator_agent.py`, `src/templates/base/ledger.json.j2` |
| 8º check del validator (ledger presente y válido) | `specs/tools.md`, `specs/validator_agent.md` | `src/tools/validate_harness.py`, `tests/test_validate_harness.py` |
| Sub-sesión aislada por tarea + ledger + rama por defecto + merge automático en CI verde | "Flujo de ejecución del harness generado" arriba | `src/templates/agents/leader.md.j2` |
| `init.sh` comprueba git/gh en vez de asumirlos | `specs/templates.md` | `src/templates/base/init.sh.j2` |

Pendiente real: `update_spec` (sin implementar, no forma parte de esta iteración).

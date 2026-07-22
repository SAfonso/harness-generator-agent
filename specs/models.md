# SPEC — módulo `models`

> Código: `src/models/harness_spec.py` · Tests: indirectos (los modelos se validan a través de los tests de tools y agentes)
> Errores conocidos: `errors/models.md` · Reglas transversales: `SPEC.md`

## Responsabilidad

Definir el estado compartido entre agentes. `HarnessSpec` es la única estructura
que viaja por todo el pipeline: `intake` la rellena parcialmente, `analysis` la
completa, `generator` la consume y `validator` la contrasta.

## Modelos

### `HarnessSpec` — estado compartido entre agentes

```python
class HarnessSpec(BaseModel):
    # Recogido por intake_agent
    project_type: str           # data_pipeline | api | web | agent | cli | other
    description: str            # descripción libre del proyecto
    stack: list[str]            # tecnologías principales
    data_sources: list[str]     # orígenes de datos o inputs
    constraints: list[str]      # limitaciones conocidas
    acceptance_criteria: list[str]  # definición de done
    deliverable: str            # qué se entrega al final
    time_available: str         # ej: "2 días", "2 semanas"

    # Decidido por analysis_agent
    agent_roles: list[AgentRole]    # roles y modos de cada agente
    harness_complexity: str         # simple | standard | complex
    rules: list[str]                # reglas específicas del harness

    # Metadatos
    mode: str                   # EJECUTOR | PROFESOR
    llm_config: LLMConfig       # configuración de modelos por agente
    generated_at: str           # timestamp
```

### `AgentRole`

```python
class AgentRole(BaseModel):
    name: str       # ej: "implementer"
    mode: str       # ej: "BISTURÍ"
    scope: str      # descripción de su responsabilidad
    tools: list[str]  # tools que puede usar
```

### `LLMConfig`

```python
class LLMConfig(BaseModel):
    strategy: str                    # same | recommended | custom
    default_model: str | None        # si strategy == "same"
    per_agent: dict[str, str]        # agente → modelo si strategy == "custom"
                                     # vacío si strategy == "recommended"
```

### `IntakeResult` — salida del intake_agent

```python
class IntakeResult(BaseModel):
    spec: HarnessSpec | None         # None si falta información crítica
    status: Literal["complete", "needs_input"]
    questions: list[str]             # preguntas pendientes si status == "needs_input"
```

---

## Modelos runtime del harness generado (v2 — spec, sin implementar)

Los siguientes modelos NO viajan por el pipeline de este repo (`intake → analysis →
generator → validator`). Describen artefactos del harness **ya generado**, en
ejecución sobre `feature_list.json`: `generator_agent` los usa para renderizar el
esqueleto (`progress/ledger.json` vacío) y `validator_agent` para comprobar su forma.
Ningún agente de `src/agents/` los instancia — los produce/consume Claude Code al
ejecutar el harness generado (ver `SPEC.md#flujo-de-ejecución-del-harness-generado`).

### `LedgerDecision` — entrada de decisión en el ledger

```python
class LedgerDecision(BaseModel):
    id: str                     # ADR-000N
    date: str
    summary: str                 # una línea, destilada
    scope: list[str]             # paths o áreas afectadas
    task_id: int | None          # tarea que originó la decisión, si aplica
```

### `IntegrationReport` — salida cruda de NOTARIO/CENTINELA dentro de la sub-sesión

```python
class IntegrationReport(BaseModel):
    task_id: int
    pushed: bool
    branch: str | None
    pr_url: str | None
    ci_status: Literal["pending", "passed", "failed"] | None
    merge_status: Literal["pending", "merged", "conflict", "failed"] | None
    failure_context: str | None   # reconstruido por CENTINELA si ci_status/merge_status fallan
```

### `TaskCloseOut` — resumen que la sub-sesión de una tarea devuelve a DIRECTOR

```python
class TaskCloseOut(BaseModel):
    task_id: int
    status: Literal["integrated", "escalated"]
    summary: str                  # resumen destilado, nunca el log crudo
    decisions: list[LedgerDecision] = []
    commit: str | None = None
    pr_url: str | None = None
    attempts: int                 # ciclos de rechazo consumidos (máx. 3)
```

### `ContextPackage` — paquete mínimo que DIRECTOR pasa a cada sub-sesión de tarea

```python
class ContextPackage(BaseModel):
    task_id: int
    task_spec: dict                              # entrada correspondiente de feature_list.json
    relevant_decisions: list[LedgerDecision]      # filtradas por scope/depends_on, no el ledger completo
    relevant_task_summaries: list[TaskCloseOut]   # solo de las tareas en depends_on
    acceptance_criteria: list[str]                # subconjunto relevante de CHECKPOINTS.md
```

### `Ledger` — estado persistente de DIRECTOR entre sesiones (`progress/ledger.json`)

```python
class Ledger(BaseModel):
    decisions: list[LedgerDecision] = []
    tasks: list[TaskCloseOut] = []
```

DIRECTOR no mantiene memoria conversacional larga entre tareas — este modelo es su
único estado persistente, versionado en el repo del proyecto destino.

## Reglas del módulo

- Todos los modelos se importan desde `src.models.harness_spec` — un único punto de import.
- Los modelos no contienen lógica de negocio: son contratos de datos puros.
- Cualquier campo nuevo debe añadirse aquí (spec) antes que en el código, y el agente
  que lo rellena debe quedar documentado en el comentario del campo.
- Los valores válidos de `project_type`, `mode` y `harness_complexity` viven en
  `src/config.py` (`PROJECT_TYPES`, `HARNESS_MODES`, `HARNESS_COMPLEXITY_LEVELS`).

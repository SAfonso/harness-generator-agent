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

## Reglas del módulo

- Todos los modelos se importan desde `src.models.harness_spec` — un único punto de import.
- Los modelos no contienen lógica de negocio: son contratos de datos puros.
- Cualquier campo nuevo debe añadirse aquí (spec) antes que en el código, y el agente
  que lo rellena debe quedar documentado en el comentario del campo.
- Los valores válidos de `project_type`, `mode` y `harness_complexity` viven en
  `src/config.py` (`PROJECT_TYPES`, `HARNESS_MODES`, `HARNESS_COMPLEXITY_LEVELS`).

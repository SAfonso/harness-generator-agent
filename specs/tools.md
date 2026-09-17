# SPEC — módulo `tools`

> Código: `src/tools/` · Tests: `tests/test_assess_input.py`, `tests/test_classify_project.py`, `tests/test_render_template.py`, `tests/test_validate_harness.py`, `tests/test_inspect_project.py`
> Errores conocidos: `errors/tools.md` · Reglas transversales: `SPEC.md`

## Responsabilidad

Funciones puras y deterministas que los agentes invocan. Ninguna tool conversa con
el usuario ni toma decisiones de diseño — eso es trabajo de los agentes.

---

## `assess_input`

**Fichero:** `src/tools/assess_input.py`

**Firma:**
```python
assess_input(text: str) -> InputAssessment
```

```python
class InputAssessment(BaseModel):
    density: Literal["rich", "sparse"]
    covered_dimensions: list[str]
    missing_dimensions: list[str]
```

**Contrato:**
- Mide la densidad de información del input del usuario contra las 7 dimensiones:
  `project_type`, `stack`, `data_sources`, `constraints`, `acceptance_criteria`,
  `deliverable`, `time_available`.
- Detección por keywords (v1). `density == "rich"` si cubre ≥ 4 dimensiones.
- `missing_dimensions` lista exactamente las dimensiones no detectadas — el
  `intake_agent` las convierte en preguntas.
- TODO v2: reemplazar keywords por clasificación LLM (sinónimos, otros idiomas).

---

## `classify_project`

**Fichero:** `src/tools/classify_project.py`

**Firma:**
```python
classify_project(spec: HarnessSpec) -> str
```

**Contrato:**
- Confirma el tipo de proyecto a partir de la `HarnessSpec` parcial.
  Devuelve uno de: `data_pipeline | api | web | agent | cli | other`.
- Puntúa keywords sobre `description + stack`.
- Si hay evidencia fuerte de un tipo distinto al elegido por el usuario, la evidencia
  gana (override). Sin señal de keywords, se respeta la elección del usuario.

---

## `render_template`

**Fichero:** `src/tools/render_template.py`

**Firma:**
```python
render_template(template_name: str, spec: HarnessSpec, agent: AgentRole | None = None) -> str
```

**Contrato:**
- Renderiza una plantilla Jinja2 desde `src/templates/` (`TEMPLATES_DIR`).
- `template_name` es ruta relativa, ej: `"base/AGENTS.md.j2"`.
- Contexto disponible: `{{ spec }}` siempre; `{{ agent }}` solo si se pasa `agent`.
- Plantilla inexistente → excepción (no falla silenciosamente).
- Ver convenciones de plantillas en `specs/templates.md`.

---

## `validate_harness`

**Fichero:** `src/tools/validate_harness.py`

**Firma:**
```python
validate_harness(harness_path: Path, spec: HarnessSpec) -> ValidationReport
```

```python
class CheckResult(BaseModel):
    check_id: int
    passed: bool
    file: str | None
    expected: str | None
    found: str | None

class ValidationReport(BaseModel):
    passed: bool
    results: list[CheckResult]
```

**Los 8 checks obligatorios (contrato canónico — `validator_agent` los referencia):**
```
1. Todos los agentes en AGENTS.md tienen su fichero en .claude/agents/
2. Todos los modos en los ficheros de agente coinciden con HarnessSpec.agent_roles
3. CHECKPOINTS.md referencia los criterios de aceptación de la entrevista
4. feature_list.json tiene al menos una tarea en estado "pending"
5. init.sh no tiene placeholders sin resolver
6. CLAUDE.md menciona explícitamente el modo del harness (EJECUTOR/PROFESOR)
7. Ningún fichero tiene el string "{{" sin cerrar
8. progress/ledger.json existe y es JSON válido con las claves "decisions" y
   "tasks" (v2; ver specs/models.md#Ledger)
```

- `passed == True` solo si los 8 checks pasan sin excepciones.
- Cada check fallido produce un `CheckResult` con qué se esperaba vs qué se encontró.

---

## `inspect_project` — ⚠️ definida en spec, implementación pendiente (brownfield, v2)

**Fichero (futuro):** `src/tools/inspect_project.py`

**Firma:**
```python
inspect_project(path: Path) -> InspectionResult
```

**Contrato:**
- Solo lectura: nunca escribe ni modifica nada en `path`.
- Detecta si `path` es un proyecto **ya empezado** (`is_existing_project`) por
  señales concretas, no por "hay algún fichero":
  - manifiestos de dependencias conocidos (`package.json`, `pyproject.toml`,
    `requirements.txt`, `Cargo.toml`, `go.mod`, `pom.xml`, ...)
  - `.git/` con al menos un commit
  - `README.md` o `CLAUDE.md` con contenido no trivial
  - Un directorio vacío, o con solo un `.git` sin commits, es
    `is_existing_project = False` — mismo comportamiento que v1 (greenfield).
- Si `is_existing_project`, intenta rellenar `InspectionResult.fields` para las
  7 dimensiones de `assess_input` (`project_type`, `stack`, `data_sources`,
  `constraints`, `acceptance_criteria`, `deliverable`, `time_available`):
  - `project_type` y `stack`: a partir de manifiestos y estructura de carpetas.
    Reutiliza las keywords de `classify_project` en vez de duplicar la
    heurística — construye una `HarnessSpec` mínima a partir de lo leído
    (manifiestos + estructura) y se la pasa a `classify_project`.
  - `data_sources`, `constraints`, `acceptance_criteria`, `deliverable`,
    `time_available`: normalmente no inferibles del código; solo se rellenan
    si hay evidencia explícita (ej. `CHECKPOINTS.md` o `feature_list.json` ya
    existentes de una ejecución previa del harness).
  - Cada campo lleva su `evidence` (qué fichero/patrón lo sustenta) y
    `confidence`: `"high"` si viene de un manifiesto explícito, `"low"` si es
    heurística débil (ej. solo el nombre de una carpeta).
  - Nunca inventa un valor sin evidencia — dimensión sin señal → ausente de
    `fields`, no un valor por defecto.
- `summary`: 3–5 líneas legibles que `intake_agent` muestra tal cual al abrir
  la conversación en modo brownfield (ver `specs/intake_agent.md`).

**Reglas:**
- No falla si `path` no es un proyecto reconocible: devuelve
  `InspectionResult(is_existing_project=False, fields={}, summary="")`, nunca
  una excepción.
- No decide el tipo de proyecto por sí sola con confianza `"high"` si las
  señales son contradictorias (ej. `package.json` de frontend y `requirements.txt`
  de un pipeline de datos en el mismo repo) — en ese caso `confidence="low"` y
  dice ambas señales en `evidence`, dejando que PROFESOR confirme con el usuario.

---

## `update_spec` — ⚠️ definida en spec, implementación en v2

**Fichero (futuro):** `src/tools/update_spec.py`

**Firma:**
```python
update_spec(section: str, new_content: str, spec_path: Path) -> bool
```

**Responsabilidad:** Actualizar una sección concreta del SPEC cuando el reviewer
detecta un fallo de diseño y el usuario aprueba el cambio.

**Flujo:**
1. `reviewer` rechaza y clasifica el rechazo como "fallo de diseño"
2. `leader` evalúa: ¿es fallo de implementación o de diseño?
3. Si fallo de diseño → escala al usuario con propuesta concreta de cambio de SPEC
4. Usuario aprueba → `leader` llama a `update_spec(section, new_content)`
5. `update_spec` actualiza el spec y regenera los tests afectados
6. `leader` relanza `implementer` con el SPEC actualizado

**Reglas:**
- Solo el `leader` puede llamar a esta tool, nunca el `reviewer` directamente.
- Cualquier cambio de SPEC requiere aprobación explícita del usuario.
- Después de actualizar el spec, los tests afectados se marcan como `pending` de revisión.
- Se registra el cambio en `progress/history.md` con timestamp y razón.

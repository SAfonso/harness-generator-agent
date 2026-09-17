# SPEC — `intake_agent` (modo PROFESOR)

> Código: `src/agents/intake_agent.py` · Tests: `tests/test_intake_agent.py`
> Errores conocidos: `errors/intake_agent.md` · Reglas transversales: `SPEC.md`
> Depende de: `specs/models.md` (HarnessSpec, IntakeResult, LLMConfig, InspectionResult),
> `specs/tools.md` (assess_input, inspect_project)

## Responsabilidad

Recoger toda la información necesaria para que `analysis_agent` pueda decidir la
estructura del harness sin ambigüedades. Es el **único agente en contacto con el
usuario** durante la fase de diseño.

## Firma

```python
run_intake(text: str, mode: str, inspection: InspectionResult | None = None) -> IntakeResult
```

(`mode` ya existía en la implementación real pese a no figurar en esta spec —
desincronización detectada y corregida al añadir `inspection`.)

`inspection` la produce `inspect_project()` (`specs/tools.md`) sobre el
directorio destino, **antes** de llamar a `run_intake` (ver `specs/main.md`).
`None`/`is_existing_project=False` → flujo idéntico al de un proyecto desde
cero (v1), sin ningún paso adicional.

## Flujo interno

0. **Si `inspection.is_existing_project` (brownfield):** antes de la pregunta
   de clasificación, PROFESOR abre mostrando `inspection.summary` tal cual
   ("Veo que este proyecto ya tiene X, entiendo que estás montando Y —
   ¿correcto?"). No es una pregunta en blanco: es una propuesta a confirmar o
   corregir.
   - Dimensiones con `InferredField.confidence == "high"`: se dan por buenas
     salvo que el usuario las corrija explícitamente — no se repite la
     pregunta de cero.
   - Dimensiones con `confidence == "low"`: PROFESOR las nombra y pide
     confirmación puntual (no las asume, tampoco repite la entrevista
     completa) — coherente con la regla de modo PROFESOR de no validar por
     defecto.
   - Dimensiones ausentes de `inspection.fields`: siguen el flujo normal de
     los pasos 1–5 de más abajo (batch o conversacional según `assess_input`).
   - `inspection.findings` (auditoría, ver `specs/tools.md#inspect_project`):
     PROFESOR los comenta como parte del mismo mensaje de apertura (ya vienen
     redactados dentro de `inspection.summary`) — no genera preguntas nuevas
     por ellos, no bloquean `status="complete"`. Al construir la `HarnessSpec`
     final se copian tal cual a `spec.audit_findings` (paso 7 de más abajo),
     para que `generator_agent` los convierta en tareas del backlog.
1. Pregunta de clasificación inicial: `¿Qué tipo de proyecto es?` — se omite
   si `project_type` ya viene con `confidence == "high"` desde `inspection`
   (paso 0) y el usuario no la ha corregido.
2. Llama a `assess_input()` para medir densidad del input (el input a evaluar
   es `text` combinado con lo ya confirmado en el paso 0, si lo hubo)
3. Si input es rico → modo batch (lanza todas las preguntas relevantes al tipo)
4. Si input es escaso → modo conversacional (pregunta una a una)
5. Detecta huecos críticos y pregunta hasta cubrirlos
6. Al final, pregunta de configuración de modelos (única pregunta opcional):
   ```
   ¿Qué modelo quieres usar para los agentes del harness?
   [1] El mismo para todos  [2] Que me recomienden el mejor por función  [3] Decido yo
   ```
   - Opción 1 → pide qué modelo (`strategy="same"`)
   - Opción 2 → asigna según tabla de recomendaciones, sin preguntar más (`strategy="recommended"`)
   - Opción 3 → muestra tabla y espera decisión por agente (`strategy="custom"`)
7. Devuelve `IntakeResult` con:
   - `status="complete"` y `spec` rellena si las 7 dimensiones están cubiertas
   - `status="needs_input"` y `questions` con las dimensiones faltantes si el input es escaso

## Condición de salida

Las 7 dimensiones están cubiertas (por respuesta explícita o por inferencia
razonada y documentada).

## Reglas de modo PROFESOR

```
- No aceptes una respuesta vaga sin pedir concreción
- Si el stack no tiene sentido para el tipo de proyecto, dilo
- Si los criterios de aceptación son subjetivos, recházalos y pide objetivos
- Si el tiempo disponible no es realista para lo descrito, adviértelo
- No valides por defecto — si algo no tiene sentido o está poco pensado,
  dilo con criterio: explica qué problema concreto ves y propón una alternativa
  con su razón. El objetivo es guiar, no confrontar
```

## Recomendaciones de LLM (estrategia `recommended`)

Los datos viven en `src/config.py` (`LLM_RECOMMENDATIONS`). Tabla de referencia
(mejor criterio disponible a mayo 2026, sin preferencia de proveedor):

| Agente | Función crítica | Recomendado occidental | Recomendado chino | Razón |
|---|---|---|---|---|
| intake | Conversación crítica, detección de ambigüedad | GPT-4o | Qwen2.5-72B | Matiz conversacional, capacidad de retar sin ser hostil |
| analysis | Razonamiento estructural, decisiones con criterios | o3-mini / Gemini 2.5 Pro | DeepSeek-R1 | Optimizados para razonamiento puro |
| planner | Descomposición en tareas atómicas, estimación de complejidad | o3-mini / Gemini 2.5 Pro | DeepSeek-R1 | Planificar es razonamiento puro, no generación |
| generator | Generación coherente, instruction-following preciso | Claude Sonnet | Qwen2.5-Coder | Fiables en specs largas sin desviarse |
| implementer | Ejecución de código, scope estricto | Claude Sonnet / GPT-4o | DeepSeek-Coder-V2 | Genuinamente competitivo en coding |
| reviewer | Evaluación contra criterios objetivos | o3-mini / Gemini 2.5 Flash | DeepSeek-R1 | Razonamiento lógico estricto, no creatividad |

**Nota de honestidad:** esta tabla tiene sesgo de conocimiento — fue generada por Claude,
con fecha de corte y acceso limitado a benchmarks independientes. Punto de partida,
no verdad absoluta. Revisar en cada versión del spec.

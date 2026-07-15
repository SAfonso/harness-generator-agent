# SPEC — `intake_agent` (modo PROFESOR)

> Código: `src/agents/intake_agent.py` · Tests: `tests/test_intake_agent.py`
> Errores conocidos: `errors/intake_agent.md` · Reglas transversales: `SPEC.md`
> Depende de: `specs/models.md` (HarnessSpec, IntakeResult, LLMConfig), `specs/tools.md` (assess_input)

## Responsabilidad

Recoger toda la información necesaria para que `analysis_agent` pueda decidir la
estructura del harness sin ambigüedades. Es el **único agente en contacto con el
usuario** durante la fase de diseño.

## Firma

```python
run_intake(text: str) -> IntakeResult
```

## Flujo interno

1. Pregunta de clasificación inicial: `¿Qué tipo de proyecto es?`
2. Llama a `assess_input()` para medir densidad del input
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

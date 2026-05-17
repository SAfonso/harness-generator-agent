# SPEC.md — harness-generator-agent

## Objetivo

Dado un input del usuario describiendo su proyecto, producir un directorio `harness/`
completamente personalizado y listo para usar con Claude Code.

---

## Arquitectura general

```
src/
├── agents/
│   ├── intake_agent.py       # PROFESOR — entrevista al usuario
│   ├── analysis_agent.py     # JUEZ — decide estructura del harness
│   ├── generator_agent.py    # ESCRIBANO — genera ficheros
│   └── validator_agent.py    # FISCAL — valida coherencia final
├── tools/
│   ├── classify_project.py   # Clasifica tipo de proyecto
│   ├── assess_input.py       # Mide densidad de información del input
│   ├── render_template.py    # Renderiza plantillas con contexto
│   └── validate_harness.py   # Verifica coherencia entre ficheros
├── templates/
│   ├── base/                 # Plantillas compartidas por todos los tipos
│   │   ├── CLAUDE.md.j2
│   │   ├── AGENTS.md.j2
│   │   ├── CHECKPOINTS.md.j2
│   │   ├── feature_list.json.j2
│   │   └── init.sh.j2
│   └── agents/               # Plantillas de agentes con modos
│       ├── leader.md.j2      # modo: DIRECTOR
│       ├── intake.md.j2      # modo: PROFESOR
│       ├── analysis.md.j2    # modo: JUEZ
│       ├── generator.md.j2   # modo: ESCRIBANO
│       ├── implementer.md.j2 # modo: BISTURÍ
│       └── reviewer.md.j2    # modo: FISCAL
├── models/
│   └── harness_spec.py       # Dataclass con toda la info recogida
├── main.py                   # Entrypoint — elige modo y lanza el flujo
└── config.py                 # Constantes, tipos de proyecto, modos
```

---

## Modelos de datos

### `HarnessSpec` — estado compartido entre agentes

```python
@dataclass
class HarnessSpec:
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
@dataclass
class AgentRole:
    name: str       # ej: "implementer"
    mode: str       # ej: "BISTURÍ"
    scope: str      # descripción de su responsabilidad
    tools: list[str]  # tools que puede usar
```

### `LLMConfig`

```python
@dataclass
class LLMConfig:
    strategy: str                    # same | recommended | custom
    default_model: str | None        # si strategy == "same"
    per_agent: dict[str, str]        # agente → modelo si strategy == "custom"
                                     # vacío si strategy == "recommended"
```

---

## Agentes

### `intake_agent` — modo PROFESOR

**Responsabilidad:** Recoger toda la información necesaria para que `analysis_agent`
pueda decidir la estructura del harness sin ambigüedades.

**Flujo interno:**
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
   - Opción 1 → pide qué modelo
   - Opción 2 → asigna según tabla de recomendaciones (sin preguntar más)
   - Opción 3 → muestra tabla y espera decisión por agente
7. Devuelve `HarnessSpec` parcial (sin `agent_roles`, `rules`, `harness_complexity`)

**Condición de salida:** Las 7 dimensiones están cubiertas (puede ser por respuesta
explícita o por inferencia razonada y documentada).

**Reglas de modo PROFESOR:**
```
- No aceptes una respuesta vaga sin pedir concreción
- Si el stack no tiene sentido para el tipo de proyecto, dilo
- Si los criterios de aceptación son subjetivos, recházalos y pide objetivos
- Si el tiempo disponible no es realista para lo descrito, adviértelo
- No des la razón por darla — el usuario prefiere ser retado
```

---

### `analysis_agent` — modo JUEZ

**Responsabilidad:** Tomar la `HarnessSpec` parcial y decidir la estructura completa
del harness: cuántos agentes, qué roles, qué modos, qué reglas.

**Flujo interno:**
1. Recibe `HarnessSpec` parcial de `intake_agent`
2. Llama a `classify_project()` para confirmar tipo
3. Aplica reglas de decisión por tipo de proyecto (ver tabla abajo)
4. Decide `harness_complexity` según tiempo disponible y scope
5. Construye lista de `AgentRole` con modos asignados
6. Genera lista de reglas específicas del harness
7. Devuelve `HarnessSpec` completa

**Reglas de decisión por tipo:**

| Tipo | Agentes mínimos | Consideraciones |
|---|---|---|
| data_pipeline | implementer, reviewer | Añadir data_validator si hay transformaciones complejas |
| api | implementer, reviewer | Añadir security_checker si hay auth |
| web | implementer, reviewer | Añadir ux_checker si hay criterios visuales |
| agent | implementer, reviewer, tester | Siempre añadir tester para loops de agente |
| cli | implementer, reviewer | Harness más simple por defecto |

**Reglas de modo JUEZ:**
```
- Decide con criterios explícitos, no por intuición
- Justifica cada rol añadido en una línea
- Si hay ambigüedad en el input, resuélvela con la opción más conservadora
- No añadas agentes por si acaso — cada rol tiene que ganarse su sitio
```

---

### `generator_agent` — modo ESCRIBANO

**Responsabilidad:** Generar todos los ficheros del harness a partir de la
`HarnessSpec` completa. Coherencia entre ficheros por encima de todo.

**Flujo interno:**
1. Recibe `HarnessSpec` completa
2. Genera ficheros en este orden (el orden importa para la coherencia):
   1. `AGENTS.md` — define todos los roles (referencia para el resto)
   2. `CHECKPOINTS.md` — criterios de aceptación (referencia para el reviewer)
   3. `feature_list.json` — backlog inicial inferido
   4. `init.sh` — verificación del entorno
   5. `.claude/agents/*.md` — un fichero por agente, en orden de flujo
   6. `CLAUDE.md` — se genera último porque debe ser coherente con TODO lo anterior;
      es el fichero que Claude Code lee primero al arrancar cualquier sesión
3. Antes de generar cada fichero, lee los ya generados
4. Si detecta contradicción, para y reporta antes de continuar

**Reglas de modo ESCRIBANO:**
```
- Nunca generes un fichero sin leer los anteriores
- Cero placeholders sin resolver — si falta info, para y pide
- Los nombres de agentes en AGENTS.md deben coincidir exactamente
  con los ficheros en .claude/agents/
- El modo de cada agente debe aparecer explícito en su fichero
```

---

### `validator_agent` — modo FISCAL

**Responsabilidad:** Verificar que el harness generado es coherente y cumple
los criterios de aceptación definidos en la entrevista.

**Checks obligatorios:**
```
1. Todos los agentes en AGENTS.md tienen su fichero en .claude/agents/
2. Todos los modos en los ficheros de agente coinciden con HarnessSpec.agent_roles
3. CHECKPOINTS.md referencia los criterios de aceptación de la entrevista
4. feature_list.json tiene al menos una tarea en estado "pending"
5. init.sh no tiene placeholders sin resolver
6. CLAUDE.md menciona explícitamente el modo del harness (EJECUTOR/PROFESOR)
7. Ningún fichero tiene el string "{{" sin cerrar
```

**Condición de aprobación:** Los 7 checks pasan sin excepciones.

**Condición de rechazo:** Cualquier check fallido genera un informe con:
- Qué check falló
- En qué fichero
- Qué se esperaba vs qué se encontró

**Reglas de modo FISCAL:**
```
- Contrasta contra el contrato, no contra tu opinión
- Rechaza con referencia explícita al check que falla
- No apruebes si tienes dudas — escala al usuario
- No busques bugs de implementación — eso es trabajo del reviewer del harness
```

---

## Recomendaciones de LLM por agente

Cuando el usuario elige estrategia `recommended`, se asignan estos modelos.
La tabla refleja el mejor criterio disponible a fecha de escritura de este spec
(mayo 2026) sin preferencia por ningún proveedor:

| Agente | Función crítica | Recomendado occidental | Recomendado chino | Razón |
|---|---|---|---|---|
| intake | Conversación crítica, detección de ambigüedad | GPT-4o | Qwen2.5-72B | Matiz conversacional, capacidad de retar sin ser hostil |
| analysis | Razonamiento estructural, decisiones con criterios | o3-mini / Gemini 2.5 Pro | DeepSeek-R1 | Optimizados para razonamiento puro |
| generator | Generación coherente, instruction-following preciso | Claude Sonnet | Qwen2.5-Coder | Fiables en specs largas sin desviarse |
| implementer | Ejecución de código, scope estricto | Claude Sonnet / GPT-4o | DeepSeek-Coder-V2 | DeepSeek-Coder-V2 genuinamente competitivo en coding |
| reviewer | Evaluación contra criterios objetivos | o3-mini / Gemini 2.5 Flash | DeepSeek-R1 | Razonamiento lógico estricto, no creatividad |

**Nota de honestidad:** esta tabla tiene sesgo de conocimiento — fue generada por Claude,
que tiene fecha de corte y acceso limitado a benchmarks independientes. Tratar como
punto de partida, no como verdad absoluta. Revisar en cada versión del spec.

---

## Entrypoint — `main.py`

```
1. Mostrar opciones de modo: [1] EJECUTOR  [2] PROFESOR
2. Recoger input inicial del usuario
3. Lanzar intake_agent con modo seleccionado
4. Lanzar analysis_agent con HarnessSpec parcial
5. Lanzar generator_agent con HarnessSpec completa
6. Lanzar validator_agent sobre harness/ generado
7. Si validator aprueba → mostrar resumen y ruta del harness
8. Si validator rechaza → mostrar informe y preguntar si reintentar
```

---

## Plantillas — convenciones

- Formato: Jinja2 (`.j2`)
- Variables disponibles en todas las plantillas: `{{ spec }}` (HarnessSpec completa)
- Las plantillas de agente tienen acceso a `{{ agent }}` (AgentRole específico)
- Las plantillas NO contienen lógica compleja — eso va en los agentes

---

## Criterios de aceptación del proyecto

1. Dado un input de tipo `data_pipeline`, el harness generado es distinto
   al generado para un input de tipo `api`
2. En modo PROFESOR, el intake_agent reta al menos una decisión del usuario
3. El validator_agent rechaza un harness con placeholders sin resolver
4. El flujo completo termina en menos de 2 minutos para un input rico
5. El harness generado puede usarse directamente en Claude Code sin modificaciones

---

## Lo que NO está en v1

- Memoria entre sesiones
- Soporte para más de 6 agentes en el harness generado
- Personalización de plantillas por el usuario
- Interfaz web
- Tests automatizados (se añaden en v2)
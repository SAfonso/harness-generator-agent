# PROJECT.md — harness-generator-agent

## Qué es

Un agente que entrevista al usuario sobre su proyecto y genera un harness multi-agente
completamente personalizado para él. No es una plantilla fija — es un agente que razona
sobre lo que le describes y decide la estructura, los roles, los modos y las reglas
que mejor se adaptan a tu caso concreto.

## Qué NO es

- No es un generador de scaffolding genérico (eso es `skill-harness-scaffold`)
- No es un chatbot de propósito general
- No sustituye al criterio del usuario — lo reta y lo complementa

## Entregable concreto

Un directorio `harness/` listo para usar en cualquier proyecto, con:

```
harness/
├── CLAUDE.md              # Rol leader + reglas + modo activo del harness
├── AGENTS.md              # Mapa de agentes, modos y flujo
├── CHECKPOINTS.md         # Criterios de aceptación derivados de la entrevista
├── feature_list.json      # Backlog inicial inferido del proyecto
├── init.sh                # Verificación del entorno
├── progress/
│   ├── current.md
│   ├── history.md
│   └── errors.md
└── .claude/
    └── agents/
        ├── leader.md          # modo: DIRECTOR
        ├── intake.md          # modo: PROFESOR
        ├── analysis.md        # modo: JUEZ
        ├── generator.md       # modo: ESCRIBANO
        ├── implementer.md     # modo: BISTURÍ
        └── reviewer.md        # modo: FISCAL
```

## Modos de operación del agente

El usuario elige al inicio:

### MODO EJECUTOR
- Confía en las decisiones del usuario
- Pregunta solo cuando hay ambigüedad bloqueante
- Objetivo: harness generado lo antes posible

### MODO PROFESOR
- No da la razón por darla
- Si ve algo subóptimo, lo dice con argumento antes de continuar
- Puede rechazar una decisión y proponer alternativa
- Objetivo: harness generado + usuario con mejor criterio técnico

## Flujo de la entrevista

```
Input inicial del usuario
        ↓
[intake_agent — PROFESOR]
        ↓
  Pregunta de clasificación: ¿qué tipo de proyecto?
  → data pipeline / API / web app / agente / CLI / otro
        ↓
  ¿Cuánta información tiene el input?
  ↓                        ↓
rico → batch             escaso → conversacional extendido
        ↓
  ¿Quedan huecos críticos?
  ↓              ↓
no → continuar   sí → preguntas de aclaración puntuales
        ↓
[analysis_agent — JUEZ]
  → decide: cuántos agentes, qué roles, qué modos, qué reglas
        ↓
[generator_agent — ESCRIBANO]
  → genera ficheros coherentes entre sí
        ↓
[validator — FISCAL]
  → contrasta contra criterios de aceptación definidos en la entrevista
        ↓
harness/ listo para usar
```

## Dimensiones que cubre la entrevista

| Dimensión | Impacto en el harness |
|---|---|
| Tipo de proyecto | Árbol de preguntas relevantes, número de agentes |
| Stack tecnológico | Convenciones de código, tools disponibles |
| Orígenes de datos | Permisos, herramientas de ingesta |
| Limitaciones conocidas | Reglas de rate limit, entorno, tiempo |
| Criterios de aceptación | Qué valida el reviewer, definición de "done" |
| Entregable final | Cómo valida el FISCAL |
| Tiempo disponible | Agresividad del harness (simple vs complejo) |

## Modos por agente (fijos, no configurables por el usuario)

| Agente | Modo | Razón |
|---|---|---|
| leader | DIRECTOR | Orquesta la ejecución, no decide sobre diseño — coordina sin entrar en el contenido |
| intake_agent | PROFESOR | Único agente en contacto con el usuario en fase de diseño |
| analysis_agent | JUEZ | Decide sin ruido, justifica en una línea |
| generator_agent | ESCRIBANO | Coherencia entre ficheros por encima de todo |
| implementer | BISTURÍ | Scope estricto, mínimo viable verificable |
| reviewer | FISCAL | Contrasta contra contrato, no busca bugs |

## Criterios de éxito del proyecto

- El harness generado es distinto para un pipeline de datos vs una API vs una web app
- El modo PROFESOR reta al menos una decisión del usuario durante la entrevista
- El FISCAL rechaza al menos un fichero durante la validación interna antes de entregar
- El harness generado puede inicializar un proyecto de hackathon en < 5 minutos

## Stack

- Python 3.12 con venv (`.venv`)
- Claude Code como runtime de agentes
- Sin dependencias externas en v1 (solo stdlib + anthropic SDK)
- Ficheros de estado en disco (sin base de datos)

## Roadmap

- **v1 (hackathon 29M):** flujo completo intake → analysis → generator → validator
- **v2:** memoria entre sesiones, personalización por dominio
- **v3:** interfaz web, exportación a otros formatos de harness

## Convenciones

- Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
- Una tarea a la vez en `in_progress`
- `SPEC.md` antes de implementar cualquier agente
- Commit después de cada agente funcional
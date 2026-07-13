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
| intake | PROFESOR | Único agente en contacto con el usuario en fase de diseño |
| analysis | JUEZ | Decide sin ruido, justifica en una línea |
| generator | ESCRIBANO | Coherencia entre ficheros por encima de todo |
| implementer | BISTURÍ | Scope estricto, mínimo viable verificable |
| reviewer | FISCAL | Contrasta contra contrato, no busca bugs |
| tester | QA | Solo para proyectos de tipo agent — verifica comportamiento antes de aprobar |

Los modos son fijos y viven en `src/config.py` (`AGENT_MODES`). Las reglas de
comportamiento de cada modo están en el spec del agente correspondiente.

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

## Lo que NO está en v1

- Memoria entre sesiones
- Soporte para más de 6 agentes en el harness generado
- Personalización de plantillas por el usuario
- Interfaz web
- `update_spec` operativo (definido en `specs/tools.md`, implementación en v2)

# SPEC — `generator_agent` (modo ESCRIBANO)

> Código: `src/agents/generator_agent.py` · Tests: `tests/test_generator_agent.py`
> Errores conocidos: `errors/generator_agent.md` · Reglas transversales: `SPEC.md`
> Depende de: `specs/models.md` (HarnessSpec), `specs/tools.md` (render_template), `specs/templates.md`

## Responsabilidad

Generar todos los ficheros del harness a partir de la `HarnessSpec` completa.
**Coherencia entre ficheros por encima de todo.**

## Firma

```python
run_generator(spec: HarnessSpec, output_dir: Path) -> list[Path]
```

## Flujo interno

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

## Reglas de modo ESCRIBANO

```
- Nunca generes un fichero sin leer los anteriores
- Cero placeholders sin resolver — si falta info, para y pide
- Los nombres de agentes en AGENTS.md deben coincidir exactamente
  con los ficheros en .claude/agents/
- El modo de cada agente debe aparecer explícito en su fichero
```

## Invariantes verificadas por tests

- Genera todos los ficheros esperados para un proyecto `api`
- Incluye `tester.md` solo para proyectos de tipo `agent`
- Ningún fichero generado contiene placeholders sin resolver (`{{`)
- Ningún fichero generado queda vacío

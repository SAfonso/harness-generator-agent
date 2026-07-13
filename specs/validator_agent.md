# SPEC — `validator_agent` (modo FISCAL)

> Código: `src/agents/validator_agent.py` (⚠️ pendiente de implementar) · Tests: `tests/test_validator_agent.py` (⚠️ pendiente — TDD: tests primero)
> Errores conocidos: `errors/validator_agent.md` · Reglas transversales: `SPEC.md`
> Depende de: `specs/models.md` (HarnessSpec), `specs/tools.md` (validate_harness)

## Responsabilidad

Verificar que el harness generado es coherente y cumple los criterios de
aceptación definidos en la entrevista.

## Firma

```python
run_validator(harness_path: Path, spec: HarnessSpec) -> ValidationReport
```

## Contrato

- Envuelve la tool `validate_harness()`, que implementa los **7 checks obligatorios**
  (contrato canónico en `specs/tools.md#validate_harness` — no duplicar aquí).
- **Condición de aprobación:** los 7 checks pasan sin excepciones.
- **Condición de rechazo:** cualquier check fallido genera un informe con:
  - Qué check falló
  - En qué fichero
  - Qué se esperaba vs qué se encontró

## Reglas de modo FISCAL

```
- Contrasta contra el contrato, no contra tu opinión
- Rechaza con referencia explícita al check que falla
- No apruebes si tienes dudas — escala al usuario
- No busques bugs de implementación — eso es trabajo del reviewer del harness
```

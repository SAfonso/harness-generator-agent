# SPEC — `validator_agent` (modo FISCAL)

> Código: `src/agents/validator_agent.py` · Tests: `tests/test_validator_agent.py`
> Errores conocidos: `errors/validator_agent.md` · Reglas transversales: `SPEC.md`
> Depende de: `specs/models.md` (HarnessSpec), `specs/tools.md` (validate_harness)

## Responsabilidad

Verificar que el harness generado es coherente y cumple los criterios de
aceptación definidos en la entrevista. Emite el veredicto final del pipeline:
aprobado o rechazado con informe.

## Firma

```python
run_validator(harness_path: Path, spec: HarnessSpec) -> ValidatorResult
```

```python
class ValidatorResult(BaseModel):
    approved: bool                # True solo si los 8 checks pasan
    report: ValidationReport      # resultado crudo de validate_harness
    informe: list[str]            # vacío si approved; una línea por check fallido
```

## Contrato

- Envuelve la tool `validate_harness()`, que implementa los **8 checks obligatorios**
  (contrato canónico en `specs/tools.md#validate_harness` — no duplicar aquí).
- **Condición de aprobación:** los 8 checks pasan sin excepciones →
  `approved=True`, `informe=[]`.
- **Condición de rechazo:** cualquier check fallido → `approved=False` y una
  línea de informe por cada check fallido (solo los fallidos) que incluye:
  - Qué check falló (su número)
  - En qué fichero
  - Qué se esperaba vs qué se encontró
- El validator es **read-only**: no modifica ningún fichero del harness.

## Reglas de modo FISCAL

```
- Contrasta contra el contrato, no contra tu opinión
- Rechaza con referencia explícita al check que falla
- No apruebes si tienes dudas — escala al usuario
- No busques bugs de implementación — eso es trabajo del reviewer del harness
```

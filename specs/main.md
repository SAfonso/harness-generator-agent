# SPEC — `main.py` (entrypoint)

> Código: `src/main.py` · Tests: `tests/test_main.py`
> Errores conocidos: `errors/main.md` · Reglas transversales: `SPEC.md`
> Depende de: los specs de los 4 agentes (`intake`, `analysis`, `generator`, `validator`)

## Responsabilidad

Orquestar el pipeline completo. No contiene lógica de negocio — solo encadena
agentes y gestiona el resultado.

## Diseño

Dos capas, para que la orquestación sea testeable sin interacción:

- **`run_pipeline()`** — orquestador puro, sin I/O de consola. Todo el flujo vive aquí.
- **`main()`** — wrapper interactivo fino (menú de modo, input del usuario,
  impresión de resultados, pregunta de reintento). Sin lógica propia.

## Firma

```python
run_pipeline(text: str, mode: str, output_dir: Path) -> PipelineResult
```

```python
class PipelineResult(BaseModel):
    status: Literal["needs_input", "approved", "rejected"]
    questions: list[str]            # solo si needs_input
    harness_path: Path | None       # output_dir / "harness" si se llegó a generar
    generated_files: list[str]      # ficheros escritos por generator
    validator: ValidatorResult | None  # veredicto FISCAL si se llegó a validar
```

## Flujo

```
1. main(): mostrar opciones de modo: [1] EJECUTOR  [2] PROFESOR
2. main(): recoger input inicial del usuario
3. run_pipeline(): run_intake(text, mode)
   → si needs_input: devolver status="needs_input" con las preguntas
     (main() las muestra, amplía el input y relanza)
4. run_pipeline(): run_analysis(spec parcial) → spec completa
5. run_pipeline(): run_generator(spec, output_dir / "harness")
6. run_pipeline(): run_validator(harness_path, spec)
7. Si validator aprueba → status="approved"; main() muestra resumen y ruta
8. Si validator rechaza → status="rejected"; main() muestra el informe
   y pregunta si reintentar
```

## Restricciones

- `run_pipeline()` no imprime ni lee de consola — toda la interacción vive en `main()`.
- Si el intake devuelve `needs_input`, **no** se crea ningún directorio ni fichero.
- El harness se genera siempre en `output_dir / "harness"`.
- El flujo completo debe terminar en menos de 2 minutos para un input rico
  (criterio de aceptación 4 del proyecto).

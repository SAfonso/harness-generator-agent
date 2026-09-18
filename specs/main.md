# SPEC — `main.py` (entrypoint)

> Código: `src/main.py` · Tests: `tests/test_main.py`
> Errores conocidos: `errors/main.md` · Reglas transversales: `SPEC.md`
> Depende de: los specs de los 4 agentes (`intake`, `analysis`, `generator`, `validator`)
> y de `specs/tools.md` (`inspect_project`, v2 brownfield)

## Responsabilidad

Orquestar el pipeline completo. No contiene lógica de negocio — solo encadena
agentes y gestiona el resultado.

## Diseño

Tres capas, para que la orquestación sea testeable sin interacción y también
invocable por un agente (Claude Code vía Bash) que no puede sostener una
conversación turno a turno con un subproceso:

- **`run_pipeline()`** — orquestador puro, sin I/O de consola. Todo el flujo vive aquí.
- **`main(argv=None)`** — punto de entrada del CLI. Parsea argumentos y
  despacha a una de las dos siguientes según si se pasó `--text`:
  - **`_run_noninteractive(text, mode, output_dir)`** — sin `input()`, una
    sola llamada a `run_pipeline()` y termina. Pensada para ser invocada por
    un agente vía Bash (`harness-agents --text "..." --mode ...`) — ver
    v2 más abajo.
  - **`_run_interactive()`** — el wrapper interactivo original (menú de
    modo, input del usuario, impresión de resultados, pregunta de
    reintento). Sin lógica propia. Es el que se usa cuando un humano teclea
    `harness-agents` directamente en su propia terminal.

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
3. run_pipeline(): inspect_project(output_dir) → InspectionResult (v2 brownfield)
   → output_dir es siempre el proyecto destino real, nunca `output_dir / "harness"`
     (ese se genera de cero en el paso 6, exista o no el proyecto)
   → si output_dir no existe o está vacío: InspectionResult(is_existing_project=False),
     idéntico a v1
4. run_pipeline(): run_intake(text, mode, inspection)
   → si needs_input: devolver status="needs_input" con las preguntas
     (main() las muestra, amplía el input y relanza; la `inspection` ya
     calculada se reutiliza, no se recalcula en el reintento)
5. run_pipeline(): run_analysis(spec parcial) → spec completa
6. run_pipeline(): run_generator(spec, output_dir / "harness")
7. run_pipeline(): run_validator(harness_path, spec)
8. Si validator aprueba → status="approved"; main() muestra resumen y ruta
9. Si validator rechaza → status="rejected"; main() muestra el informe
   y pregunta si reintentar
```

## Restricciones

- `run_pipeline()` no imprime ni lee de consola — toda la interacción vive en `main()`.
- Si el intake devuelve `needs_input`, **no** se crea ningún directorio ni fichero.
- El harness se genera siempre en `output_dir / "harness"`.
- El flujo completo debe terminar en menos de 2 minutos para un input rico
  (criterio de aceptación 4 del proyecto).

## v2 — modo no interactivo (`--text`)

**Bug real que motiva esto** (`errors/main.md`): `_run_interactive()` usa
`input()` bloqueante. Cuando algo la invoca vía el tool de Bash de Claude
Code (una llamada de subproceso, sin stdin sostenido turno a turno), la
primera llamada a `input()` revienta con `EOFError` — la skill
`skill/harness-agents/SKILL.md` prometía "invócala desde Claude Code" pero
eso literalmente no funcionaba.

**Firma:**
```python
main(argv: list[str] | None = None) -> None
```

Flags (todas opcionales; sin `--text`, comportamiento idéntico a v1):
- `--text TEXT` — descripción del proyecto. Si está presente, `main()`
  despacha a `_run_noninteractive()` en vez de `_run_interactive()`.
- `--mode {EJECUTOR,PROFESOR}` — por defecto `EJECUTOR`. Solo se usa junto a `--text`.
- `--output-dir PATH` — por defecto `Path.cwd()`. Solo se usa junto a `--text`.

**`_run_noninteractive(text, mode, output_dir)`:**
- Llama a `run_pipeline()` **una sola vez** — sin bucle de reintento (no hay
  `input()` para ampliar el texto ni para preguntar si reintentar).
- `status="needs_input"` → imprime las dimensiones que faltan y hace
  `raise SystemExit(1)` — quien invocó (agente o humano) debe volver a
  llamar con un `--text` ampliado; es una invocación nueva, no una
  continuación de la anterior.
- `status="approved"` → imprime la ruta del harness y el nº de ficheros,
  termina con éxito (código 0).
- `status="rejected"` → imprime el informe del validator y hace
  `raise SystemExit(1)` — no hay reintento automático.
- Esto convierte a Claude Code (cuando ejecuta la skill) en la capa
  conversacional: es Claude quien pregunta al usuario en el chat, arma el
  `--text`, y reintenta con más texto si `needs_input` — el CLI en sí nunca
  vuelve a intentar leer de stdin.

# Errores conocidos — módulo `main`

> Spec del módulo: `specs/main.md` · Errores transversales y protocolo completo: `errors/ERRORS.md`

Antes de depurar un error en este módulo: busca aquí. Si lo resuelves y no estaba,
regístralo con este formato (la entrada más reciente arriba):

```markdown
## [YYYY-MM-DD] Título corto del error
**Síntoma:** mensaje de error o comportamiento observado
**Causa:** causa raíz, no el síntoma
**Solución:** pasos concretos aplicados
**Prevención:** (opcional) cómo evitar que vuelva a ocurrir
```

---

<!-- Entradas debajo de esta línea, la más reciente arriba -->

## [2026-09-18] harness-agents da EOFError al invocarse desde un agente vía Bash
**Síntoma:** ejecutar `harness-agents` desde el tool de Bash de Claude Code
(no desde una terminal real tecleada por un humano) revienta en el primer
prompt:
```
Modo del harness: [1] EJECUTOR  [2] PROFESOR
> Traceback (most recent call last):
  ...
    mode = "PROFESOR" if input("> ").strip() == "2" else "EJECUTOR"
EOFError: EOF when reading a line
```
Descubierto en producción: un usuario intentó usar la skill `/harness-agents`
sobre un proyecto real (`AutoOncle`) y la sesión de Claude Code que la
invocó se quedó sin poder continuar.
**Causa:** `main()` (antes `_run_interactive()`, sin ese nombre todavía)
solo tenía una ruta, construida enteramente sobre `input()` bloqueante. El
tool de Bash de un agente ejecuta un subproceso de una sola vez sin stdin
sostenido turno a turno — no hay forma de "seguir tecleando respuestas" en
llamadas sucesivas. La skill (`skill/harness-agents/SKILL.md`) prometía
"invócala desde Claude Code" pero eso nunca pudo funcionar tal como estaba.
**Solución:** `main(argv=None)` ahora despacha a `_run_noninteractive(text,
mode, output_dir)` si se pasa `--text` (nunca llama a `input()`, una sola
pasada por `run_pipeline()`, código de salida no-cero si `needs_input` o
`rejected`) o a `_run_interactive()` (el comportamiento original) si no.
`skill/harness-agents/SKILL.md` actualizada para que Claude construya el
`--text` en el propio chat (preguntando al usuario ahí, no vía stdin del
subproceso) y reintente con más texto si hace falta.
**Prevención:** cualquier entrypoint pensado para invocarse "desde Claude
Code" debe evitar `input()`/bucles interactivos en el proceso que se lanza
por Bash — la conversación vive en el chat de Claude, no en el subproceso.

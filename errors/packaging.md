# Errores conocidos — módulo `packaging`

> Spec del módulo: `specs/packaging.md` · Errores transversales y protocolo completo: `errors/ERRORS.md`

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

## [2026-09-17] SKILL.md instruía python3 -m src.main, generando el harness en el repo equivocado
**Síntoma:** siguiendo `skill/harness-agents/SKILL.md` tal como se escribió
originalmente ("desde la raíz del repo clonado: `python3 -m src.main`"), el
harness se generaría dentro de `harness-generator-agent` en vez de en el
proyecto real del usuario — justo el caso de uso brownfield que la skill
existe para cubrir. No se llegó a ejecutar en producción: se detectó al
responder una pregunta del usuario sobre cómo usar la skill en un proyecto ya
empezado.
**Causa:** `run_pipeline(text, mode, output_dir)` usa `Path.cwd()` (en `main()`)
como `output_dir` — el proyecto destino. `python3 -m src.main` necesita `cwd`
en la raíz del repo del generador para que `import src` resuelva (Python añade
el cwd a `sys.path` con `-m`), lo que fuerza `output_dir` al lugar equivocado.
El entry point instalado por pip (`harness-agents`) no tiene esta restricción:
funciona desde cualquier `cwd` porque el paquete ya está en `site-packages`/
enlace editable.
**Solución:** `SKILL.md` reescrita para instalar (`pip install -e <repo>` si
`harness-agents` no está ya en PATH) y ejecutar siempre el entry point
instalado, nunca el módulo en crudo, con el `cwd` puesto en el proyecto del
usuario. `specs/packaging.md` y `tests/test_packaging.py` actualizados para
que el contrato lo exija explícitamente.
**Prevención:** cualquier canal de arranque de este generador (skill, doc,
alias) debe pasar por el entry point instalado — nunca `python3 -m src.main`
en crudo fuera del propio repo. `tests/test_packaging.py` falla si `SKILL.md`
vuelve a instruirlo.

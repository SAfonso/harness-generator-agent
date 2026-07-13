# Errores conocidos — módulo `tools`

> Spec del módulo: `specs/tools.md` · Errores transversales y protocolo completo: `errors/ERRORS.md`

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

## [2026-07-13] Check 7 de validate_harness da falsos positivos en proyectos brownfield
**Síntoma:** al validar un harness aplicado sobre un proyecto ya empezado
(DataPipeline-PreRAG), check 7 rechaza por `{{` sin balancear en ficheros que no
son del harness: `graphify-out/graph.html`, docs, hooks de `.git`, caches.
**Causa:** check 7 hace `rglob('*')` sobre todo el directorio — fue diseñado para
un `harness/` recién generado donde todos los ficheros salen de plantillas. En un
proyecto vivo hay ficheros preexistentes con `{{` legítimos.
**Solución (workaround):** validar checks 1–6 sobre la raíz del proyecto y check 7
solo sobre los ficheros gestionados por el harness (CLAUDE.md, AGENTS.md,
CHECKPOINTS.md, feature_list.json, init.sh, `.claude/agents/*.md`).
**Prevención:** cambio de diseño pendiente para v2 (vía spec, `specs/tools.md`):
check 7 debería recibir la lista de ficheros generados (o excluir `.git/` y todo
lo no gestionado) en vez de escanear el árbol completo. Relacionado: modo
brownfield no soportado en v1.

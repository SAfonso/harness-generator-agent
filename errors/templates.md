# Errores conocidos — módulo `templates`

> Spec del módulo: `specs/templates.md` · Errores transversales y protocolo completo: `errors/ERRORS.md`

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

## [2026-09-23] Los agentes generados no se registraban como subagentes
**Síntoma:** en el proyecto destino (AutoOncle) `/agents` no listaba leader/planner/etc. y el harness no se podía invocar, aunque `.claude/agents/*.md` existían. Además, ninguna regla hacía que Claude pasara por el leader.
**Causa:** las plantillas `agents/*.md.j2` empezaban directamente con el título, sin la cabecera YAML (`name`, `description`) que Claude Code exige para registrar un subagente. El spec de `templates` no lo mencionaba (gap de spec, no solo de implementación).
**Solución:** cabecera `name: {{ agent.name }}` / `description: {{ agent.scope }}` en todas las plantillas de agente, sin `model` (lo decide el leader por tarea). `CLAUDE.md.j2` gana `## Cómo trabajar` (todo cambio pasa por el leader) y `leader.md.j2` gana `## Instrucción nueva del usuario` (entrevista estilo PROFESOR antes de planificar). Ver `specs/templates.md`.
**Prevención:** tests en `tests/test_generator_agent.py` comprueban la cabecera de cada agente generado. Si un `scope` pasara a contener `: ` o `#`, habría que entrecomillarlo en la plantilla.

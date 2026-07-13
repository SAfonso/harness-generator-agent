# Errores conocidos — GENERAL (transversales)

Errores que afectan a más de un módulo o al entorno del proyecto (dependencias,
configuración, pytest, imports, git). Los errores propios de un módulo van en
`errors/<modulo>.md`.

## Protocolo (obligatorio)

1. **Al encontrar un error** trabajando en un módulo: leer **primero**
   `errors/<modulo>.md` y después este fichero.
2. **Si el error ya está documentado** → aplicar la solución registrada. No
   re-investigar desde cero.
3. **Si es nuevo** → resolverlo y, antes de dar la tarea por terminada,
   documentarlo con el formato de abajo:
   - en `errors/<modulo>.md` si es específico del módulo
   - aquí si es transversal (afecta a ≥ 2 módulos o al entorno)
4. Una entrada por error raíz — si un síntoma nuevo tiene la misma causa que una
   entrada existente, ampliar esa entrada en lugar de duplicarla.

## Formato de entrada

```markdown
## [YYYY-MM-DD] Título corto del error
**Síntoma:** mensaje de error o comportamiento observado (literal si es posible)
**Causa:** causa raíz, no el síntoma
**Solución:** pasos concretos aplicados
**Prevención:** (opcional) cómo evitar que vuelva a ocurrir
```

---

<!-- Entradas debajo de esta línea, la más reciente arriba -->

*Sin errores registrados todavía.*

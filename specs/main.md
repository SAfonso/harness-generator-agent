# SPEC — `main.py` (entrypoint)

> Código: `src/main.py` (⚠️ pendiente de implementar) · Tests: pendientes — TDD: tests primero
> Errores conocidos: `errors/main.md` · Reglas transversales: `SPEC.md`
> Depende de: los specs de los 4 agentes (`intake`, `analysis`, `generator`, `validator`)

## Responsabilidad

Orquestar el pipeline completo. No contiene lógica de negocio — solo encadena
agentes y gestiona el resultado.

## Flujo

```
1. Mostrar opciones de modo: [1] EJECUTOR  [2] PROFESOR
2. Recoger input inicial del usuario
3. Lanzar intake_agent con modo seleccionado
4. Lanzar analysis_agent con HarnessSpec parcial
5. Lanzar generator_agent con HarnessSpec completa
6. Lanzar validator_agent sobre harness/ generado
7. Si validator aprueba → mostrar resumen y ruta del harness
8. Si validator rechaza → mostrar informe y preguntar si reintentar
```

## Restricciones

- No implementar hasta que **todos** los agentes tengan sus tests en verde
  (regla TDD transversal, ver `SPEC.md`).
- El flujo completo debe terminar en menos de 2 minutos para un input rico
  (criterio de aceptación 4 del proyecto).

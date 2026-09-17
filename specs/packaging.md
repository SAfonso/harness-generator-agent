# SPEC — `packaging` (distribución de este repo)

> Código: `pyproject.toml`, `skill/harness-agents/SKILL.md` · Tests: `tests/test_packaging.py`
> Errores conocidos: `errors/packaging.md` · Reglas transversales: `SPEC.md`

## Responsabilidad

Definir cómo se instala y se arranca **este generador** (no el harness que produce)
en una máquina o proyecto nuevo. No introduce lógica: son ficheros de distribución
que envuelven `src/` tal cual, sin duplicarlo.

Dos canales, una sola fuente de verdad (`src/`):

1. **Paquete pip** — para uso como CLI standalone, fuera de Claude Code.
2. **Skill de Claude Code** — para invocarlo con `/harness-agents` desde cualquier
   proyecto abierto en Claude Code, sin paso de instalación explícito.

---

## Canal 1 — paquete pip

**Fichero:** `pyproject.toml` (raíz del repo)

**Contrato:**
- Nombre del paquete: `harness-agents`.
- Entry point de consola: `harness-agents = src.main:main`.
- Dependencias: `pydantic`, `jinja2` (las mismas que documenta `README.md`,
  hoy instaladas a mano).
- `requires-python`: `>=3.12` (versión usada en desarrollo, ver `PROJECT.md`).
- Instalación: `pip install -e .` desde la raíz del repo. Publicación a PyPI
  queda fuera de alcance de v2 (roadmap v3, ver `PROJECT.md`).
- Build backend: `setuptools` (sin dependencias de build adicionales). Requiere
  `src/__init__.py` (vacío) para que `src` sea descubrible como paquete regular
  — hoy solo sus subpaquetes (`src/agents/`, `src/tools/`, `src/models/`) lo
  tienen.

## Canal 2 — skill de Claude Code

**Fichero:** `skill/harness-agents/SKILL.md`

**Contrato:**
- Es un wrapper fino: no vendoriza ni copia `src/`, lo referencia por ruta
  relativa al repo clonado.
- Al invocarse (`/harness-agents`):
  1. Comprueba que `pydantic` y `jinja2` están disponibles en el intérprete
     activo; si falta alguna, la instala (`pip install pydantic jinja2`) antes
     de continuar — nunca falla en silencio ni asume que ya están.
  2. Ejecuta `python3 -m src.main` con el cwd puesto en la raíz del repo.
- No requiere el paquete pip instalado (canal 1) para funcionar — es una vía
  independiente sobre el mismo código, pensada para quien ya tiene el repo
  clonado y quiere arrancarlo sin salir de Claude Code.
- Es responsabilidad de la skill, no del pipeline (`src/main.py`), resolver
  la ruta del repo — `run_pipeline`/`main()` no saben si se invocan desde pip
  o desde la skill.

---

## Reglas del módulo

- `pyproject.toml` y `skill/harness-agents/SKILL.md` apuntan siempre al mismo
  `src/main:main` — un cambio de firma en `main()` (`specs/main.md`) obliga a
  revisar ambos.
- Ninguno de los dos canales contiene lógica de negocio: si hace falta lógica
  nueva, va en `src/`, no en el `SKILL.md` ni en scripts de `pyproject.toml`.
- La skill es la vía recomendada para uso dentro de Claude Code; el paquete pip
  es la vía para uso fuera de Claude Code (otros runtimes, CI, scripting).

## Testing

- `tests/test_packaging.py` valida estructura, no comportamiento interactivo:
  - `pyproject.toml` parsea (`tomllib`) y declara `name == "harness-agents"`,
    el entry point `harness-agents` apuntando a `src.main:main`, y
    `pydantic`/`jinja2` como dependencias.
  - `skill/harness-agents/SKILL.md` existe y su contenido referencia
    `src.main` (o `python3 -m src.main`) como forma de arranque.
- No se testea la instalación real (`pip install -e .`) ni la ejecución de la
  skill dentro de Claude Code — eso es verificación manual, fuera del alcance
  de pytest.

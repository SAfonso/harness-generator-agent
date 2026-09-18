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
- `run_pipeline(text, mode, output_dir)` usa `output_dir` — en `main()`,
  `Path.cwd()` en el momento de ejecutar — como el proyecto **destino**
  (donde se inspecciona y se genera `harness/`). Por eso la skill **nunca**
  ejecuta `python3 -m src.main` directamente: ese invocación exige `cwd` en
  la raíz del propio repo del generador para que `import src` resuelva, lo
  que pondría `output_dir` en el repo del generador en vez de en el proyecto
  del usuario — justo el escenario que rompe el caso de uso brownfield.
- Al invocarse (`/harness-agents`), con el `cwd` ya puesto en el proyecto del
  **usuario** (nunca en el repo del generador):
  1. Comprueba que el comando `harness-agents` (canal 1, pip) está disponible
     (`command -v harness-agents`); si no, lo instala en modo editable desde
     el repo clonado del generador (`pip install -e <ruta-del-repo>`) — eso
     arrastra `pydantic`/`jinja2` como dependencias declaradas en
     `pyproject.toml`, sin instalarlas sueltas.
  2. **Nunca ejecuta `harness-agents` a secas.** Reúne la descripción del
     proyecto preguntando al usuario en el propio chat (Claude es la capa
     conversacional, no el subproceso — ver bug real en `errors/main.md`:
     `harness-agents` sin `--text` usa `input()`, que revienta con
     `EOFError` al invocarse desde el tool de Bash de un agente, que no
     sostiene stdin turno a turno) y ejecuta
     `harness-agents --text "<descripción>" --mode <EJECUTOR|PROFESOR>
     --output-dir "$(pwd)"` sin tocar `cwd` — así `Path.cwd()` sigue siendo
     el proyecto del usuario.
  3. Si el comando termina con código de salida distinto de cero y la salida
     incluye "Falta información sobre estas dimensiones", pregunta al
     usuario por cada una en el chat, amplía `--text` con las respuestas, y
     vuelve a invocar — es una llamada nueva, no una continuación (`specs/main.md#v2`).
- Sí depende del paquete pip (canal 1) para funcionar — a diferencia del
  diseño original, la skill no reimplementa el arranque: instala y usa el
  mismo entry point que un usuario de pip tendría.

---

## Reglas del módulo

- `pyproject.toml` declara el entry point (`src.main:main`) y `skill/harness-agents/SKILL.md`
  usa siempre ese entry point ya instalado (`harness-agents`), nunca el módulo
  en crudo (`python3 -m src.main`) — un cambio de firma en `main()`
  (`specs/main.md`) obliga a revisar ambos.
- Ninguno de los dos canales contiene lógica de negocio: si hace falta lógica
  nueva, va en `src/`, no en el `SKILL.md` ni en scripts de `pyproject.toml`.
- La skill es la vía recomendada para uso dentro de Claude Code; el paquete pip
  es la vía para uso fuera de Claude Code (otros runtimes, CI, scripting).

## Testing

- `tests/test_packaging.py` valida estructura, no comportamiento interactivo:
  - `pyproject.toml` parsea (`tomllib`) y declara `name == "harness-agents"`,
    el entry point `harness-agents` apuntando a `src.main:main`, y
    `pydantic`/`jinja2` como dependencias.
  - `skill/harness-agents/SKILL.md` existe, referencia el comando instalado
    `harness-agents` como forma de arranque, e incluye `pip install -e` como
    instalación de respaldo — y **nunca** instruye `python3 -m src.main`
    como forma de arrancar (ver bug documentado en `errors/packaging.md`).
  - El fichero incluye `--text` en su ejemplo de arranque, y **nunca**
    presenta `harness-agents` a secas (sin `--text`) como forma de
    invocarse desde la skill — ese uso revienta con `EOFError`
    (`errors/main.md`).
- No se testea la instalación real (`pip install -e .`) ni la ejecución de la
  skill dentro de Claude Code — eso es verificación manual, fuera del alcance
  de pytest.

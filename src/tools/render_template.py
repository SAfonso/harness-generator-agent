from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from src.models.harness_spec import HarnessSpec, AgentRole

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def render_template(
    template_name: str,
    spec: HarnessSpec,
    agent: AgentRole | None = None,
) -> str:
    """
    Renderiza una plantilla Jinja2 con el contexto del proyecto.
    template_name: ruta relativa desde src/templates/ ej: "base/AGENTS.md.j2"
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )

    template = env.get_template(template_name)

    context = {
        "spec": spec,
        "agent": agent,
    }

    return template.render(context)


# TODO v2: añadir caché de templates para mejorar rendimiento
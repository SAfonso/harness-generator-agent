"""generator_agent — renders the harness files from a complete HarnessSpec."""

from pathlib import Path

from src.models.harness_spec import HarnessSpec
from src.tools.render_template import TEMPLATES_DIR, render_template


def _write(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)


def run_generator(spec: HarnessSpec, output_path: Path) -> list[str]:
    generated: list[str] = []

    base_files = [
        ("AGENTS.md",              "base/AGENTS.md.j2"),
        ("CHECKPOINTS.md",         "base/CHECKPOINTS.md.j2"),
        ("feature_list.json",      "base/feature_list.json.j2"),
        ("progress/ledger.json",   "base/ledger.json.j2"),
        ("init.sh",                "base/init.sh.j2"),
    ]
    for filename, template_name in base_files:
        content = render_template(template_name, spec)
        generated.append(_write(output_path / filename, content))

    for role in spec.agent_roles:
        template_name = f"agents/{role.name}.md.j2"
        if not (TEMPLATES_DIR / template_name).is_file():
            template_name = "agents/implementer.md.j2"
        content = render_template(template_name, spec, agent=role)
        generated.append(
            _write(output_path / ".claude" / "agents" / f"{role.name}.md", content)
        )

    # CLAUDE.md is always last — coherent with everything generated above
    content = render_template("base/CLAUDE.md.j2", spec)
    generated.append(_write(output_path / "CLAUDE.md", content))

    return generated

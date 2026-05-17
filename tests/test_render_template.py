"""Unit tests for render_template."""

import pytest
from jinja2.exceptions import TemplateNotFound

from src.models.harness_spec import AgentRole, HarnessSpec, LLMConfig
from src.tools import render_template as render_template_module
from src.tools.render_template import render_template


def _make_spec(**overrides) -> HarnessSpec:
    defaults = dict(
        project_type="other",
        description="",
        stack=[],
        data_sources=[],
        constraints=[],
        acceptance_criteria=[],
        deliverable="",
        time_available="",
        mode="EJECUTOR",
        llm_config=LLMConfig(strategy="same", default_model="gpt-4o"),
    )
    defaults.update(overrides)
    return HarnessSpec(**defaults)


def test_simple_template_renders_spec_description(tmp_path, monkeypatch):
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    (base_dir / "test.md.j2").write_text(
        "Proyecto: {{ spec.description }}", encoding="utf-8"
    )
    monkeypatch.setattr(render_template_module, "TEMPLATES_DIR", tmp_path)

    spec = _make_spec(description="agente que entrevista al usuario")
    output = render_template("base/test.md.j2", spec)

    assert "agente que entrevista al usuario" in output
    assert output.startswith("Proyecto: ")


def test_agent_template_renders_agent_name_and_mode(tmp_path, monkeypatch):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "test_agent.md.j2").write_text(
        "Agente: {{ agent.name }} — modo: {{ agent.mode }}", encoding="utf-8"
    )
    monkeypatch.setattr(render_template_module, "TEMPLATES_DIR", tmp_path)

    spec = _make_spec(description="x")
    agent = AgentRole(
        name="implementer",
        mode="BISTURÍ",
        scope="src/",
        tools=["Read", "Edit"],
    )
    output = render_template("agents/test_agent.md.j2", spec, agent=agent)

    assert "Agente: implementer" in output
    assert "modo: BISTURÍ" in output


def test_missing_template_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(render_template_module, "TEMPLATES_DIR", tmp_path)
    spec = _make_spec()

    with pytest.raises(TemplateNotFound):
        render_template("does/not/exist.md.j2", spec)

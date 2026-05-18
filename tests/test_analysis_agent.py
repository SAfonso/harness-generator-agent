"""Unit tests for run_analysis — written before implementation (TDD)."""

from src.agents.analysis_agent import run_analysis
from src.models.harness_spec import AgentRole, HarnessSpec, LLMConfig


def _make_partial_spec(**overrides) -> HarnessSpec:
    defaults = dict(
        project_type="api",
        description="test",
        stack=[],
        data_sources=[],
        constraints=[],
        acceptance_criteria=[],
        deliverable="",
        time_available="2 semanas",
        mode="EJECUTOR",
        llm_config=LLMConfig(strategy="same", default_model="gpt-4o"),
    )
    defaults.update(overrides)
    return HarnessSpec(**defaults)


def _assert_common_invariants(spec: HarnessSpec) -> None:
    assert spec.harness_complexity is not None
    assert spec.agent_roles, "agent_roles must not be empty"
    for role in spec.agent_roles:
        assert isinstance(role, AgentRole)
        assert role.name
        assert role.mode
        assert role.scope
        assert isinstance(role.tools, list)


def test_minimal_cli_short_time_is_simple_with_two_agents():
    partial = _make_partial_spec(project_type="cli", time_available="1 día")

    result = run_analysis(partial)

    _assert_common_invariants(result)
    assert result.harness_complexity == "simple"
    names = [r.name for r in result.agent_roles]
    assert "implementer" in names
    assert "reviewer" in names
    assert len(result.agent_roles) == 2


def test_full_api_spec_is_standard_with_rules():
    partial = _make_partial_spec(
        project_type="api",
        time_available="2 semanas",
        stack=["fastapi"],
        data_sources=["postgres"],
        acceptance_criteria=["responde en menos de 200ms"],
        deliverable="api rest desplegada",
    )

    result = run_analysis(partial)

    _assert_common_invariants(result)
    assert result.harness_complexity == "standard"
    names = [r.name for r in result.agent_roles]
    assert "implementer" in names
    assert "reviewer" in names
    assert result.rules, "rules must not be empty for a full api spec"


def test_hackathon_time_forces_simple_complexity():
    partial = _make_partial_spec(project_type="web", time_available="2 días")

    result = run_analysis(partial)

    _assert_common_invariants(result)
    assert result.harness_complexity == "simple"


def test_agent_project_always_adds_tester():
    partial = _make_partial_spec(project_type="agent", time_available="2 semanas")

    result = run_analysis(partial)

    _assert_common_invariants(result)
    names = [r.name for r in result.agent_roles]
    assert "implementer" in names
    assert "reviewer" in names
    assert "tester" in names
    assert len(result.agent_roles) == 3

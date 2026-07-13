"""Unit tests for run_validator — written before implementation (TDD)."""

import json
from pathlib import Path

import pytest

from src.agents.validator_agent import run_validator
from src.models.harness_spec import AgentRole, HarnessSpec, LLMConfig


@pytest.fixture
def spec() -> HarnessSpec:
    return HarnessSpec(
        project_type="api",
        description="test",
        stack=[],
        data_sources=[],
        constraints=[],
        acceptance_criteria=["funciona correctamente"],
        deliverable="",
        time_available="",
        mode="EJECUTOR",
        agent_roles=[
            AgentRole(name="implementer", mode="BISTURÍ", scope="implementa", tools=[]),
            AgentRole(name="reviewer", mode="FISCAL", scope="revisa", tools=[]),
        ],
        llm_config=LLMConfig(strategy="same", default_model="gpt-4o"),
    )


@pytest.fixture
def valid_harness(tmp_path) -> Path:
    (tmp_path / "CLAUDE.md").write_text(
        "Harness en modo EJECUTOR — listo para usar.", encoding="utf-8"
    )
    (tmp_path / "CHECKPOINTS.md").write_text(
        "Criterio: el harness funciona correctamente.", encoding="utf-8"
    )
    (tmp_path / "feature_list.json").write_text(
        json.dumps([{"id": 1, "title": "tarea", "status": "pending"}]),
        encoding="utf-8",
    )
    (tmp_path / "init.sh").write_text(
        "#!/bin/bash\necho 'init ok'\n", encoding="utf-8"
    )
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "implementer.md").write_text(
        "Agente implementer — modo BISTURÍ", encoding="utf-8"
    )
    (agents_dir / "reviewer.md").write_text(
        "Agente reviewer — modo FISCAL", encoding="utf-8"
    )
    return tmp_path


def test_valid_harness_is_approved_with_empty_informe(valid_harness, spec):
    result = run_validator(valid_harness, spec)

    assert result.approved is True
    assert result.informe == []
    assert result.report.passed is True
    assert len(result.report.results) == 7


def test_missing_agent_file_is_rejected_with_informe_for_check_1(valid_harness, spec):
    (valid_harness / ".claude" / "agents" / "implementer.md").unlink()

    result = run_validator(valid_harness, spec)

    assert result.approved is False
    assert len(result.informe) >= 1
    line_check_1 = next(line for line in result.informe if "1" in line)
    assert "implementer" in line_check_1


def test_informe_has_one_line_per_failed_check_only(valid_harness, spec):
    # Provoca exactamente dos fallos: check 5 (placeholder en init.sh)
    # y check 7 ("{{" sin cerrar en el mismo fichero)
    (valid_harness / "init.sh").write_text(
        "#!/bin/bash\necho 'hello {{PROJECT_NAME'\n", encoding="utf-8"
    )

    result = run_validator(valid_harness, spec)
    failed_checks = [r for r in result.report.results if not r.passed]

    assert result.approved is False
    assert len(result.informe) == len(failed_checks)


def test_informe_lines_include_file_expected_and_found(valid_harness, spec):
    (valid_harness / "init.sh").write_text(
        "#!/bin/bash\necho 'hello {{PROJECT_NAME}}'\n", encoding="utf-8"
    )

    result = run_validator(valid_harness, spec)
    check_5 = next(r for r in result.report.results if r.check_id == 5)
    line_5 = next(line for line in result.informe if "init.sh" in line)

    assert result.approved is False
    assert check_5.expected in line_5
    assert check_5.found in line_5


def test_validator_does_not_modify_the_harness(valid_harness, spec):
    before = {
        p: p.read_text(encoding="utf-8")
        for p in valid_harness.rglob("*")
        if p.is_file()
    }

    run_validator(valid_harness, spec)

    after = {
        p: p.read_text(encoding="utf-8")
        for p in valid_harness.rglob("*")
        if p.is_file()
    }
    assert before == after

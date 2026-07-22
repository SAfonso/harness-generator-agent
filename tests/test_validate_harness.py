"""Unit tests for validate_harness."""

import json
from pathlib import Path

import pytest

from src.models.harness_spec import AgentRole, HarnessSpec, LLMConfig
from src.tools.validate_harness import validate_harness


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
    (tmp_path / "progress").mkdir()
    (tmp_path / "progress" / "ledger.json").write_text(
        json.dumps({"decisions": [], "tasks": []}), encoding="utf-8"
    )
    return tmp_path


def test_valid_harness_passes_all_eight_checks(valid_harness, spec):
    report = validate_harness(valid_harness, spec)

    assert report.passed is True
    assert len(report.results) == 8
    assert all(r.passed for r in report.results)


def test_missing_ledger_fails_check_8(valid_harness, spec):
    (valid_harness / "progress" / "ledger.json").unlink()

    report = validate_harness(valid_harness, spec)

    assert report.passed is False
    check_8 = next(r for r in report.results if r.check_id == 8)
    assert check_8.passed is False


def test_ledger_with_invalid_json_fails_check_8(valid_harness, spec):
    (valid_harness / "progress" / "ledger.json").write_text(
        "not valid json", encoding="utf-8"
    )

    report = validate_harness(valid_harness, spec)

    assert report.passed is False
    check_8 = next(r for r in report.results if r.check_id == 8)
    assert check_8.passed is False


def test_ledger_missing_required_keys_fails_check_8(valid_harness, spec):
    (valid_harness / "progress" / "ledger.json").write_text(
        json.dumps({"decisions": []}), encoding="utf-8"
    )

    report = validate_harness(valid_harness, spec)

    assert report.passed is False
    check_8 = next(r for r in report.results if r.check_id == 8)
    assert check_8.passed is False


def test_missing_implementer_agent_file_fails_check_1(valid_harness, spec):
    (valid_harness / ".claude" / "agents" / "implementer.md").unlink()

    report = validate_harness(valid_harness, spec)

    assert report.passed is False
    check_1 = next(r for r in report.results if r.check_id == 1)
    assert check_1.passed is False


def test_init_sh_with_unresolved_placeholder_fails_check_5(valid_harness, spec):
    (valid_harness / "init.sh").write_text(
        "#!/bin/bash\necho 'hello {{PROJECT_NAME}}'\n", encoding="utf-8"
    )

    report = validate_harness(valid_harness, spec)

    assert report.passed is False
    check_5 = next(r for r in report.results if r.check_id == 5)
    assert check_5.passed is False


def test_feature_list_without_pending_tasks_fails_check_4(valid_harness, spec):
    (valid_harness / "feature_list.json").write_text(
        json.dumps([{"id": 1, "title": "tarea", "status": "done"}]),
        encoding="utf-8",
    )

    report = validate_harness(valid_harness, spec)

    assert report.passed is False
    check_4 = next(r for r in report.results if r.check_id == 4)
    assert check_4.passed is False

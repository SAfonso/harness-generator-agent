"""Unit tests for the v2 runtime models (ledger, context package, integration
report) — written before implementation (TDD). Ver specs/models.md."""

import pytest
from pydantic import ValidationError

from src.models.harness_spec import (
    ContextPackage,
    IntegrationReport,
    Ledger,
    LedgerDecision,
    TaskCloseOut,
)


def test_ledger_decision_requires_scope_as_list():
    decision = LedgerDecision(
        id="ADR-0001",
        date="2026-07-22",
        summary="Se decide usar rama por tarea",
        scope=["src/agents/generator_agent.py"],
        task_id=3,
    )

    assert decision.task_id == 3
    assert decision.scope == ["src/agents/generator_agent.py"]


def test_ledger_decision_task_id_defaults_to_none():
    decision = LedgerDecision(
        id="ADR-0002", date="2026-07-22", summary="x", scope=[]
    )

    assert decision.task_id is None


def test_task_close_out_rejects_invalid_status():
    with pytest.raises(ValidationError):
        TaskCloseOut(
            task_id=1,
            status="done",  # inválido: solo integrated | escalated
            summary="x",
            attempts=1,
        )


def test_task_close_out_defaults_are_empty():
    close_out = TaskCloseOut(
        task_id=1, status="integrated", summary="tarea integrada", attempts=1
    )

    assert close_out.decisions == []
    assert close_out.commit is None
    assert close_out.pr_url is None


def test_integration_report_accepts_failure_context_on_failed_ci():
    report = IntegrationReport(
        task_id=5,
        pushed=True,
        branch="task/5-fix-parser",
        pr_url="https://github.com/example/repo/pull/9",
        ci_status="failed",
        merge_status="failed",
        failure_context="job 'tests' falló: AssertionError en test_parser.py:12",
    )

    assert report.ci_status == "failed"
    assert "AssertionError" in report.failure_context


def test_integration_report_rejects_invalid_merge_status():
    with pytest.raises(ValidationError):
        IntegrationReport(
            task_id=5,
            pushed=True,
            merge_status="approved",  # inválido
        )


def test_context_package_bundles_only_relevant_history():
    decision = LedgerDecision(
        id="ADR-0001", date="2026-07-22", summary="x", scope=["src/"]
    )
    prior_task = TaskCloseOut(
        task_id=1, status="integrated", summary="tarea previa", attempts=1
    )

    package = ContextPackage(
        task_id=2,
        task_spec={"id": 2, "title": "siguiente tarea", "depends_on": [1]},
        relevant_decisions=[decision],
        relevant_task_summaries=[prior_task],
        acceptance_criteria=["responde en menos de 200ms"],
    )

    assert package.task_spec["depends_on"] == [1]
    assert package.relevant_task_summaries[0].task_id == 1


def test_ledger_defaults_to_empty_lists():
    ledger = Ledger()

    assert ledger.decisions == []
    assert ledger.tasks == []


def test_ledger_accumulates_task_close_outs():
    close_out = TaskCloseOut(
        task_id=1, status="integrated", summary="x", attempts=1
    )

    ledger = Ledger(tasks=[close_out])

    assert len(ledger.tasks) == 1
    assert ledger.tasks[0].status == "integrated"

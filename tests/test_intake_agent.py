"""Unit tests for run_intake — written before implementation (TDD)."""

from src.agents.intake_agent import run_intake
from src.models.harness_spec import HarnessSpec, IntakeResult


def test_rich_input_returns_complete_with_filled_spec():
    text = (
        "Quiero construir un pipeline de datos con spark y databricks. "
        "Los datos vienen de S3. Sin restricciones de red. "
        "Done cuando el pipeline procesa 1000 registros sin errores. "
        "Entrego un script python. Tengo 2 días."
    )

    result = run_intake(text, mode="EJECUTOR")

    assert isinstance(result, IntakeResult)
    assert result.status == "complete"
    assert result.spec is not None
    assert isinstance(result.spec, HarnessSpec)
    assert result.questions == []
    assert result.spec.mode == "EJECUTOR"


def test_sparse_input_returns_needs_input_with_no_spec():
    text = "quiero hacer algo con python"

    result = run_intake(text, mode="EJECUTOR")

    assert result.status == "needs_input"
    assert result.spec is None
    assert len(result.questions) > 0


def test_boundary_input_returns_only_missing_dimensions_in_questions():
    text = (
        "pipeline de datos con spark. Entrego un script. "
        "Tengo 1 semana. Done cuando no hay errores."
    )

    result = run_intake(text, mode="EJECUTOR")

    assert result.status == "needs_input"
    # questions lists only missing dimensions, not all seven
    assert len(result.questions) < 7
    assert "data_sources" in result.questions
    assert "constraints" in result.questions
    # dimensions clearly covered by the input must NOT be in questions
    assert "project_type" not in result.questions
    assert "stack" not in result.questions
    assert "acceptance_criteria" not in result.questions
    assert "deliverable" not in result.questions


def test_rich_input_with_recommended_llm_strategy():
    text = (
        "Quiero construir un pipeline de datos con spark y databricks. "
        "Los datos vienen de S3. Sin restricciones de red. "
        "Done cuando el pipeline procesa 1000 registros sin errores. "
        "Entrego un script python. Tengo 2 días. "
        "Para los modelos usa la estrategia recommended."
    )

    result = run_intake(text, mode="EJECUTOR")

    assert result.status == "complete"
    assert result.spec is not None
    assert result.spec.llm_config.strategy == "recommended"

"""Unit tests for classify_project."""

from src.models.harness_spec import HarnessSpec, LLMConfig
from src.tools.classify_project import classify_project


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


def test_pipeline_evidence_confirms_data_pipeline():
    spec = _make_spec(
        description="pipeline de datos con spark y delta lake",
        stack=["spark", "databricks"],
        project_type="data_pipeline",
    )

    assert classify_project(spec) == "data_pipeline"


def test_no_keyword_signal_respects_user_choice():
    spec = _make_spec(
        description="sistema genérico",
        stack=["numpy"],
        project_type="cli",
    )

    assert classify_project(spec) == "cli"


def test_strong_evidence_overrides_user_choice():
    spec = _make_spec(
        description="api rest con fastapi y endpoints json",
        stack=["fastapi"],
        project_type="web",
    )

    assert classify_project(spec) == "api"

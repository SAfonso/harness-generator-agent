"""Unit tests for run_pipeline — written before implementation (TDD)."""

import src.main as main_module
from src.main import PipelineResult, run_pipeline

RICH_PIPELINE_TEXT = (
    "Quiero construir un pipeline de datos con spark y databricks. "
    "Los datos vienen de S3. Sin restricciones de red. "
    "Done cuando el pipeline procesa 1000 registros sin errores. "
    "Entrego un script python. Tengo 2 días."
)

RICH_AGENT_TEXT = (
    "Quiero construir un agente autónomo con llm en python. "
    "Los datos vienen de una base de datos. Sin restricciones. "
    "Done cuando el agente resuelve 10 tareas seguidas. "
    "Entrego un script python. Tengo 2 semanas."
)


def test_rich_input_ends_approved_with_generated_harness(tmp_path):
    result = run_pipeline(RICH_PIPELINE_TEXT, mode="EJECUTOR", output_dir=tmp_path)

    assert isinstance(result, PipelineResult)
    assert result.status == "approved"
    assert result.harness_path == tmp_path / "harness"
    assert (result.harness_path / "CLAUDE.md").is_file()
    assert result.validator is not None
    assert result.validator.approved is True
    assert len(result.generated_files) > 0


def test_sparse_input_returns_needs_input_without_generating(tmp_path):
    result = run_pipeline("quiero hacer algo con python", mode="EJECUTOR", output_dir=tmp_path)

    assert result.status == "needs_input"
    assert len(result.questions) > 0
    assert result.harness_path is None
    assert result.validator is None
    assert list(tmp_path.iterdir()) == []


def test_agent_project_harness_includes_tester(tmp_path):
    result = run_pipeline(RICH_AGENT_TEXT, mode="EJECUTOR", output_dir=tmp_path)

    assert result.status == "approved"
    assert (result.harness_path / ".claude" / "agents" / "tester.md").is_file()


def test_broken_generation_is_rejected_with_informe(tmp_path, monkeypatch):
    real_generator = main_module.run_generator

    def broken_generator(spec, output_path):
        generated = real_generator(spec, output_path)
        init_sh = output_path / "init.sh"
        init_sh.write_text(
            init_sh.read_text(encoding="utf-8") + "\necho '{{PENDIENTE}}'\n",
            encoding="utf-8",
        )
        return generated

    monkeypatch.setattr(main_module, "run_generator", broken_generator)

    result = run_pipeline(RICH_PIPELINE_TEXT, mode="EJECUTOR", output_dir=tmp_path)

    assert result.status == "rejected"
    assert result.validator is not None
    assert result.validator.approved is False
    assert any("init.sh" in line for line in result.validator.informe)

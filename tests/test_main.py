"""Unit tests for run_pipeline — written before implementation (TDD)."""

import pytest

import src.main as main_module
from src.main import PipelineResult, main, run_pipeline

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


def test_brownfield_output_dir_lets_intake_infer_project_type(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")
    text = (
        "Los datos vienen de una base de datos. Sin restricciones. "
        "Done cuando funciona. Entrego un informe. Tengo 3 días."
    )

    result = run_pipeline(text, mode="EJECUTOR", output_dir=tmp_path)

    assert result.status == "approved"
    assert result.harness_path == tmp_path / "harness"


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


def test_main_with_text_flag_runs_noninteractively_and_approves(tmp_path, capsys):
    main([
        "--text", RICH_PIPELINE_TEXT,
        "--mode", "EJECUTOR",
        "--output-dir", str(tmp_path),
    ])

    captured = capsys.readouterr()
    assert "aprobado" in captured.out.lower()
    assert (tmp_path / "harness" / "CLAUDE.md").is_file()


def test_main_with_text_flag_defaults_to_ejecutor_mode(tmp_path):
    main(["--text", RICH_PIPELINE_TEXT, "--output-dir", str(tmp_path)])

    assert (tmp_path / "harness" / "CLAUDE.md").is_file()


def test_main_with_text_flag_exits_nonzero_on_needs_input(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--text", "quiero hacer algo con python", "--output-dir", str(tmp_path)])

    assert exc_info.value.code != 0
    captured = capsys.readouterr()
    assert "falta" in captured.out.lower()
    assert list(tmp_path.iterdir()) == []


def test_main_without_text_flag_still_uses_interactive_path(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("input() invocado — confirma que sigue siendo la ruta interactiva")

    monkeypatch.setattr("builtins.input", _boom)

    with pytest.raises(AssertionError):
        main([])

"""Unit tests for inspect_project — written before implementation (TDD)."""

import subprocess

from src.tools.inspect_project import inspect_project


def _git_init_with_commit(path):
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    (path / "README.md").write_text("proyecto de prueba con contenido real, no un stub vacío", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)


def test_empty_directory_is_not_an_existing_project(tmp_path):
    result = inspect_project(tmp_path)

    assert result.is_existing_project is False
    assert result.fields == {}
    assert result.summary == ""


def test_git_history_and_readme_mark_existing_project_without_type_signal(tmp_path):
    _git_init_with_commit(tmp_path)

    result = inspect_project(tmp_path)

    assert result.is_existing_project is True
    assert "project_type" not in result.fields
    assert "stack" not in result.fields
    assert result.summary != ""


def test_requirements_txt_with_fastapi_infers_api_with_high_confidence(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")

    result = inspect_project(tmp_path)

    assert result.is_existing_project is True
    assert result.fields["project_type"].value == "api"
    assert result.fields["project_type"].confidence == "high"
    assert "requirements.txt" in result.fields["project_type"].evidence
    assert "Python" in result.fields["stack"].value


def test_requirements_txt_with_pyspark_infers_data_pipeline(tmp_path):
    (tmp_path / "requirements.txt").write_text("pyspark\napache-airflow\n", encoding="utf-8")

    result = inspect_project(tmp_path)

    assert result.fields["project_type"].value == "data_pipeline"
    assert result.fields["project_type"].confidence == "high"


def test_contradictory_manifests_yield_low_confidence(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "^18.0.0"}}', encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("pyspark\napache-airflow\n", encoding="utf-8")

    result = inspect_project(tmp_path)

    assert result.fields["project_type"].confidence == "low"
    assert "package.json" in result.fields["project_type"].evidence
    assert "requirements.txt" in result.fields["project_type"].evidence


def test_manifest_without_keyword_signal_leaves_project_type_absent(tmp_path):
    (tmp_path / "go.mod") .write_text("module example.com/foo\n\ngo 1.22\n", encoding="utf-8")

    result = inspect_project(tmp_path)

    assert result.is_existing_project is True
    assert "project_type" not in result.fields
    assert result.fields["stack"].value == ["Go"]
    assert result.fields["stack"].confidence == "high"


def test_inspect_project_never_raises_on_unreadable_path(tmp_path):
    missing = tmp_path / "does-not-exist"

    result = inspect_project(missing)

    assert result.is_existing_project is False

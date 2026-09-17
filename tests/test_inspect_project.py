"""Unit tests for inspect_project — written before implementation (TDD)."""

import subprocess

from src.tools.inspect_project import inspect_project


def _git_init_with_commit(path, with_remote=False):
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    (path / "README.md").write_text("proyecto de prueba con contenido real, no un stub vacío", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)
    if with_remote:
        subprocess.run(
            ["git", "remote", "add", "origin", "https://example.com/repo.git"],
            cwd=path, check=True,
        )


def _findings_by_check(result):
    return {finding.check: finding for finding in result.findings}


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


def test_manifest_without_git_flags_no_git_repo_as_blocking(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")

    result = inspect_project(tmp_path)

    findings = _findings_by_check(result)
    assert findings["no_git_repo"].severity == "blocking"
    assert "no_git_remote" not in findings


def test_git_without_remote_flags_no_git_remote_as_blocking(tmp_path):
    _git_init_with_commit(tmp_path, with_remote=False)

    result = inspect_project(tmp_path)

    findings = _findings_by_check(result)
    assert findings["no_git_remote"].severity == "blocking"
    assert "no_git_repo" not in findings


def test_git_with_remote_has_no_git_findings(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    _git_init_with_commit(tmp_path, with_remote=True)

    result = inspect_project(tmp_path)

    findings = _findings_by_check(result)
    assert "no_git_repo" not in findings
    assert "no_git_remote" not in findings


def test_missing_tests_and_ci_are_flagged_as_warnings(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    _git_init_with_commit(tmp_path, with_remote=True)

    result = inspect_project(tmp_path)

    findings = _findings_by_check(result)
    assert findings["no_tests"].severity == "warning"
    assert findings["no_ci"].severity == "warning"


def test_existing_tests_and_ci_suppress_those_findings(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    _git_init_with_commit(tmp_path, with_remote=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_smoke.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\n", encoding="utf-8")

    result = inspect_project(tmp_path)

    findings = _findings_by_check(result)
    assert "no_tests" not in findings
    assert "no_ci" not in findings


def test_empty_docs_flagged_when_no_readme_or_claude_md(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")

    result = inspect_project(tmp_path)

    findings = _findings_by_check(result)
    assert findings["empty_docs"].severity == "warning"


def test_non_trivial_readme_suppresses_empty_docs_finding(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "Este proyecto hace algo concreto y está documentado con detalle.",
        encoding="utf-8",
    )

    result = inspect_project(tmp_path)

    findings = _findings_by_check(result)
    assert "empty_docs" not in findings


def test_code_quality_review_recommended_when_manifests_present(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")

    result = inspect_project(tmp_path)

    findings = _findings_by_check(result)
    assert findings["code_quality_review_pending"].severity == "warning"
    assert "/code-review" in findings["code_quality_review_pending"].suggested_fix


def test_no_code_quality_finding_without_manifests(tmp_path):
    _git_init_with_commit(tmp_path, with_remote=True)

    result = inspect_project(tmp_path)

    findings = _findings_by_check(result)
    assert "code_quality_review_pending" not in findings

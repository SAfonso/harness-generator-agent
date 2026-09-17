"""Structural tests for packaging — written before implementation (TDD)."""

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _pyproject():
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_pyproject_declares_package_name_and_entry_point():
    pyproject = _pyproject()

    assert pyproject["project"]["name"] == "harness-agents"
    assert pyproject["project"]["scripts"]["harness-agents"] == "src.main:main"


def test_pyproject_declares_dependencies():
    dependencies = " ".join(_pyproject()["project"]["dependencies"]).lower()

    assert "pydantic" in dependencies
    assert "jinja2" in dependencies


def test_pyproject_requires_python_3_12_or_newer():
    assert _pyproject()["project"]["requires-python"] == ">=3.12"


def test_skill_file_exists_and_points_to_src_main():
    skill_path = REPO_ROOT / "skill" / "harness-agents" / "SKILL.md"

    assert skill_path.is_file()
    assert "src.main" in skill_path.read_text(encoding="utf-8")

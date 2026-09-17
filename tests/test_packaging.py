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


def test_skill_file_uses_the_installed_entry_point_not_the_raw_module():
    skill_path = REPO_ROOT / "skill" / "harness-agents" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")

    assert skill_path.is_file()
    assert "pip install -e" in content
    # el comando de arranque real es el entry point instalado, no el módulo
    # en crudo (bug real documentado en errors/packaging.md)
    assert "```bash\nharness-agents\n```" in content
    assert "```bash\npython3 -m src.main\n```" not in content

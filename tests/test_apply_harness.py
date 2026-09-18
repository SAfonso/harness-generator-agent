"""Unit tests for apply_harness — written before implementation (TDD)."""

from src.tools.apply_harness import apply_harness


def _make_staged_harness(harness_path):
    harness_path.mkdir(parents=True)
    (harness_path / "CLAUDE.md").write_text("# CLAUDE generado", encoding="utf-8")
    (harness_path / "AGENTS.md").write_text("# AGENTS", encoding="utf-8")
    (harness_path / "feature_list.json").write_text("[]", encoding="utf-8")
    agents_dir = harness_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "leader.md").write_text("# leader", encoding="utf-8")
    progress_dir = harness_path / "progress"
    progress_dir.mkdir()
    (progress_dir / "ledger.json").write_text('{"decisions": [], "tasks": []}', encoding="utf-8")


def test_applies_everything_directly_to_root_when_no_existing_claude_md(tmp_path):
    harness_path = tmp_path / "harness"
    _make_staged_harness(harness_path)

    applied = apply_harness(harness_path, tmp_path)

    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "# CLAUDE generado"
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / "feature_list.json").is_file()
    assert (tmp_path / ".claude" / "agents" / "leader.md").is_file()
    assert (tmp_path / "progress" / "ledger.json").is_file()
    assert not harness_path.exists()
    assert str(tmp_path / "CLAUDE.md") in applied
    assert str(tmp_path / ".claude" / "agents" / "leader.md") in applied


def test_never_overwrites_an_existing_claude_md(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# CLAUDE del usuario, no tocar", encoding="utf-8")
    harness_path = tmp_path / "harness"
    _make_staged_harness(harness_path)

    applied = apply_harness(harness_path, tmp_path)

    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "# CLAUDE del usuario, no tocar"
    assert (tmp_path / "CLAUDE.harness.md").read_text(encoding="utf-8") == "# CLAUDE generado"
    assert str(tmp_path / "CLAUDE.harness.md") in applied
    assert not harness_path.exists()


def test_merges_into_an_existing_claude_dir_without_nesting(tmp_path):
    existing_claude_dir = tmp_path / ".claude"
    existing_claude_dir.mkdir()
    (existing_claude_dir / "settings.local.json").write_text("{}", encoding="utf-8")
    harness_path = tmp_path / "harness"
    _make_staged_harness(harness_path)

    apply_harness(harness_path, tmp_path)

    assert (tmp_path / ".claude" / "settings.local.json").is_file()
    assert (tmp_path / ".claude" / "agents" / "leader.md").is_file()
    assert not (tmp_path / ".claude" / ".claude").exists()


def test_removes_staging_directory_after_applying(tmp_path):
    harness_path = tmp_path / "harness"
    _make_staged_harness(harness_path)

    apply_harness(harness_path, tmp_path)

    assert not harness_path.exists()

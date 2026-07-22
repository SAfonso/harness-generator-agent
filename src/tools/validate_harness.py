"""Validate a generated harness against its HarnessSpec."""

import json
from pathlib import Path

from pydantic import BaseModel

from src.models.harness_spec import HarnessSpec


class CheckResult(BaseModel):
    check_id: int
    passed: bool
    file: str | None = None
    expected: str | None = None
    found: str | None = None


class ValidationReport(BaseModel):
    passed: bool
    results: list[CheckResult]


def validate_harness(harness_path: Path, spec: HarnessSpec) -> ValidationReport:
    results: list[CheckResult] = []

    # Check 1: every agent in spec has its file under .claude/agents/
    agents_dir = harness_path / ".claude" / "agents"
    missing = [a.name for a in spec.agent_roles if not (agents_dir / f"{a.name}.md").exists()]
    results.append(
        CheckResult(
            check_id=1,
            passed=not missing,
            file=str(agents_dir),
            expected=", ".join(f"{a.name}.md" for a in spec.agent_roles) or None,
            found=("missing: " + ", ".join(missing)) if missing else "all present",
        )
    )

    # Check 2: each agent's .md file declares the mode defined in its AgentRole
    mismatched: list[str] = []
    for agent in spec.agent_roles:
        agent_file = agents_dir / f"{agent.name}.md"
        if not agent_file.exists():
            continue
        if agent.mode not in agent_file.read_text(encoding="utf-8"):
            mismatched.append(f"{agent.name}({agent.mode})")
    results.append(
        CheckResult(
            check_id=2,
            passed=not mismatched,
            file=str(agents_dir),
            expected="mode declared in each agent file",
            found=("mismatch: " + ", ".join(mismatched)) if mismatched else "all match",
        )
    )

    # Check 3: CHECKPOINTS.md contains at least one acceptance criterion
    checkpoints_file = harness_path / "CHECKPOINTS.md"
    found_criterion: str | None = None
    if checkpoints_file.exists():
        content = checkpoints_file.read_text(encoding="utf-8")
        for criterion in spec.acceptance_criteria:
            if criterion in content:
                found_criterion = criterion
                break
    results.append(
        CheckResult(
            check_id=3,
            passed=found_criterion is not None,
            file=str(checkpoints_file),
            expected="at least one acceptance criterion",
            found=found_criterion if found_criterion else "none of the criteria present",
        )
    )

    # Check 4: feature_list.json has at least one task with status "pending"
    feature_file = harness_path / "feature_list.json"
    has_pending = False
    found_statuses: list[str] = []
    if feature_file.exists():
        try:
            data = json.loads(feature_file.read_text(encoding="utf-8"))
            tasks = data if isinstance(data, list) else data.get("tasks", [])
            for task in tasks:
                if isinstance(task, dict) and "status" in task:
                    found_statuses.append(task["status"])
                    if task["status"] == "pending":
                        has_pending = True
        except json.JSONDecodeError:
            found_statuses = ["<invalid JSON>"]
    results.append(
        CheckResult(
            check_id=4,
            passed=has_pending,
            file=str(feature_file),
            expected='task with status "pending"',
            found=", ".join(found_statuses) if found_statuses else "no tasks found",
        )
    )

    # Check 5: init.sh does not contain "{{"
    init_file = harness_path / "init.sh"
    init_exists = init_file.exists()
    contains_placeholder = init_exists and "{{" in init_file.read_text(encoding="utf-8")
    results.append(
        CheckResult(
            check_id=5,
            passed=init_exists and not contains_placeholder,
            file=str(init_file),
            expected='no "{{" placeholder',
            found=(
                "file not found"
                if not init_exists
                else ('"{{" present' if contains_placeholder else "clean")
            ),
        )
    )

    # Check 6: CLAUDE.md contains the harness mode (EJECUTOR or PROFESOR)
    claude_file = harness_path / "CLAUDE.md"
    has_mode = claude_file.exists() and spec.mode in claude_file.read_text(encoding="utf-8")
    results.append(
        CheckResult(
            check_id=6,
            passed=has_mode,
            file=str(claude_file),
            expected=spec.mode,
            found=spec.mode if has_mode else "mode token missing",
        )
    )

    # Check 7: every "{{" across the harness has a matching "}}"
    unbalanced: list[str] = []
    for path in harness_path.rglob("*"):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if content.count("{{") != content.count("}}"):
            unbalanced.append(str(path.relative_to(harness_path)))
    results.append(
        CheckResult(
            check_id=7,
            passed=not unbalanced,
            file=", ".join(unbalanced) if unbalanced else None,
            expected='balanced "{{" / "}}" pairs',
            found=("unbalanced in: " + ", ".join(unbalanced)) if unbalanced else "all balanced",
        )
    )

    # Check 8: progress/ledger.json exists, is valid JSON, and has the keys
    # "decisions" and "tasks" (v2 — ver specs/models.md#Ledger)
    ledger_file = harness_path / "progress" / "ledger.json"
    ledger_found = "file not found"
    ledger_ok = False
    if ledger_file.exists():
        try:
            ledger_data = json.loads(ledger_file.read_text(encoding="utf-8"))
            if (
                isinstance(ledger_data, dict)
                and "decisions" in ledger_data
                and "tasks" in ledger_data
            ):
                ledger_ok = True
                ledger_found = "valid ledger"
            else:
                ledger_found = "missing 'decisions'/'tasks' keys"
        except json.JSONDecodeError:
            ledger_found = "invalid JSON"
    results.append(
        CheckResult(
            check_id=8,
            passed=ledger_ok,
            file=str(ledger_file),
            expected='valid JSON with "decisions" and "tasks" keys',
            found=ledger_found,
        )
    )

    return ValidationReport(passed=all(r.passed for r in results), results=results)


# TODO v2: reemplazar con clasificación LLM para mayor precisión

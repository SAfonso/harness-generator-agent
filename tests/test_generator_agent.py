"""Unit tests for run_generator — written before implementation (TDD)."""

from pathlib import Path

from src.agents.generator_agent import run_generator
from src.models.harness_spec import AgentRole, HarnessSpec, LLMConfig


def _make_complete_spec(**overrides) -> HarnessSpec:
    defaults = dict(
        project_type="api",
        description="API REST para gestión de pedidos",
        stack=["fastapi", "postgres"],
        data_sources=["postgres"],
        constraints=["sin acceso a internet"],
        acceptance_criteria=["responde en menos de 200ms"],
        deliverable="api rest desplegada",
        time_available="2 semanas",
        mode="EJECUTOR",
        harness_complexity="standard",
        rules=[
            "Una tarea a la vez en in_progress",
            "Solo el reviewer puede marcar done",
        ],
        llm_config=LLMConfig(strategy="same", default_model="gpt-4o"),
        agent_roles=[
            AgentRole(name="leader", mode="DIRECTOR",
                      scope="Orquesta la ejecución", tools=[]),
            AgentRole(name="planner", mode="ARQUITECTO",
                      scope="Descompone en tareas atómicas", tools=[]),
            AgentRole(name="implementer", mode="BISTURÍ",
                      scope="Implementa las tareas", tools=[]),
            AgentRole(name="reviewer", mode="FISCAL",
                      scope="Revisa el output", tools=[]),
            AgentRole(name="integrator", mode="NOTARIO",
                      scope="Formaliza en git el trabajo aprobado", tools=[]),
            AgentRole(name="watchman", mode="CENTINELA",
                      scope="Verifica CI y merge tras la integración", tools=[]),
        ],
    )
    defaults.update(overrides)
    return HarnessSpec(**defaults)


def test_generator_creates_all_expected_files_for_api_project(tmp_path: Path):
    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    expected = [
        tmp_path / "AGENTS.md",
        tmp_path / "CHECKPOINTS.md",
        tmp_path / "feature_list.json",
        tmp_path / "progress" / "ledger.json",
        tmp_path / "init.sh",
        tmp_path / "CLAUDE.md",
        tmp_path / ".claude" / "agents" / "leader.md",
        tmp_path / ".claude" / "agents" / "planner.md",
        tmp_path / ".claude" / "agents" / "implementer.md",
        tmp_path / ".claude" / "agents" / "reviewer.md",
        tmp_path / ".claude" / "agents" / "integrator.md",
        tmp_path / ".claude" / "agents" / "watchman.md",
    ]
    for path in expected:
        assert path.exists(), f"missing generated file: {path}"
        assert path.is_file()


def test_integrator_and_watchman_files_declare_their_own_mode(tmp_path: Path):
    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    integrator_content = (tmp_path / ".claude" / "agents" / "integrator.md").read_text(
        encoding="utf-8"
    )
    watchman_content = (tmp_path / ".claude" / "agents" / "watchman.md").read_text(
        encoding="utf-8"
    )
    assert "NOTARIO" in integrator_content
    assert "CENTINELA" in watchman_content


def test_leader_file_documents_ledger_and_context_package(tmp_path: Path):
    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    leader_content = (tmp_path / ".claude" / "agents" / "leader.md").read_text(
        encoding="utf-8"
    )
    assert "ledger" in leader_content.lower()
    assert "contextpackage" in leader_content.lower().replace(" ", "")
    assert "centinela" in leader_content.lower()


def test_init_sh_checks_git_and_gh_availability(tmp_path: Path):
    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    content = (tmp_path / "init.sh").read_text(encoding="utf-8")
    assert "git" in content
    assert "gh" in content
    assert "gh auth status" in content


def test_reviewer_file_documents_centinela_reopen(tmp_path: Path):
    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    reviewer_content = (tmp_path / ".claude" / "agents" / "reviewer.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "centinela" in reviewer_content
    assert "failure_context" in reviewer_content


def test_watchman_file_distinguishes_conflict_from_generic_ci_failure(tmp_path: Path):
    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    watchman_content = (tmp_path / ".claude" / "agents" / "watchman.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "conflicto de merge" in watchman_content
    assert "resolving-merge-conflicts" in watchman_content


def test_reviewer_file_requires_intent_tracing_for_merge_conflicts(tmp_path: Path):
    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    reviewer_content = (tmp_path / ".claude" / "agents" / "reviewer.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "conflicto de merge" in reviewer_content
    assert "intención" in reviewer_content
    assert "--ours" in reviewer_content


def test_implementer_file_documents_merge_conflict_resolution_discipline(tmp_path: Path):
    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    implementer_content = (tmp_path / ".claude" / "agents" / "implementer.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "resolving-merge-conflicts" in implementer_content
    assert "intención" in implementer_content


def test_reviewer_file_scopes_itself_to_spec_axis_and_recommends_code_review(tmp_path: Path):
    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    reviewer_content = (tmp_path / ".claude" / "agents" / "reviewer.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "eje spec" in reviewer_content
    assert "eje standards" in reviewer_content
    assert "/code-review" in reviewer_content


def test_implementer_file_requires_repro_and_hypotheses_before_retrying(tmp_path: Path):
    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    implementer_content = (tmp_path / ".claude" / "agents" / "implementer.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "diagnosing-bugs" in implementer_content
    assert "hipótesis" in implementer_content


def test_ledger_is_generated_empty(tmp_path: Path):
    import json

    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    ledger = json.loads((tmp_path / "progress" / "ledger.json").read_text(encoding="utf-8"))
    assert ledger == {"decisions": [], "tasks": []}


def test_feature_list_tasks_are_atomic_with_complexity(tmp_path: Path):
    import json

    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    tasks = json.loads((tmp_path / "feature_list.json").read_text(encoding="utf-8"))
    for task in tasks:
        assert task.get("complejidad") in ("alta", "media", "baja"), (
            f"task {task.get('id')} sin complejidad válida"
        )
    # El entregable no entra como tarea de implementación monolítica:
    # entra como tarea de descomposición del planner
    titles = " ".join(t["title"].lower() for t in tasks)
    assert "descompon" in titles


def _agent_file(tmp_path: Path, name: str) -> str:
    return (tmp_path / ".claude" / "agents" / f"{name}.md").read_text(encoding="utf-8").lower()


def test_implementer_requires_fresh_evidence_before_delivering(tmp_path: Path):
    run_generator(_make_complete_spec(), tmp_path)

    content = _agent_file(tmp_path, "implementer")
    assert "evidencia" in content
    assert "debería pasar" in content  # citado como lo que nunca se acepta


def test_reviewer_does_not_trust_the_implementers_report(tmp_path: Path):
    run_generator(_make_complete_spec(), tmp_path)

    content = _agent_file(tmp_path, "reviewer")
    assert "no se fía" in content
    assert "diff" in content


def test_integrator_only_commits_with_fresh_evidence(tmp_path: Path):
    run_generator(_make_complete_spec(), tmp_path)

    content = _agent_file(tmp_path, "integrator")
    assert "evidencia" in content


def test_leader_escalates_model_tier_with_a_fresh_session_before_the_user(tmp_path: Path):
    run_generator(_make_complete_spec(), tmp_path)

    content = _agent_file(tmp_path, "leader")
    assert "sub-sesión nueva" in content
    assert "tier" in content


def test_planner_has_a_lower_bound_on_task_size(tmp_path: Path):
    run_generator(_make_complete_spec(), tmp_path)

    content = _agent_file(tmp_path, "planner")
    assert "sobre-dividir" in content
    assert "no mezcla planificar, implementar y documentar" not in content


def test_integrator_checks_for_a_clean_working_tree_before_branching(tmp_path: Path):
    run_generator(_make_complete_spec(), tmp_path)

    content = _agent_file(tmp_path, "integrator")
    assert "git status --porcelain" in content
    assert "stash" in content  # solo para prohibirlo


def test_watchman_deletes_the_task_branch_after_a_successful_merge(tmp_path: Path):
    run_generator(_make_complete_spec(), tmp_path)

    content = _agent_file(tmp_path, "watchman")
    assert "borra la rama" in content


def test_constraints_and_data_sources_reach_checkpoints_and_agents(tmp_path: Path):
    spec = _make_complete_spec(
        constraints=["Sin acceso a internet."],
        data_sources=["postgres"],
    )

    run_generator(spec, tmp_path)

    checkpoints = (tmp_path / "CHECKPOINTS.md").read_text(encoding="utf-8")
    assert "## Restricciones" in checkpoints
    assert "Sin acceso a internet." in checkpoints
    assert "## Fuentes de datos" in checkpoints
    assert "postgres" in checkpoints

    for agent in ("planner", "implementer", "reviewer"):
        assert "sin acceso a internet." in _agent_file(tmp_path, agent), agent
    for agent in ("planner", "implementer"):
        assert "postgres" in _agent_file(tmp_path, agent), agent

    assert "restricción declarada" in _agent_file(tmp_path, "reviewer")


def test_empty_constraints_and_data_sources_leave_no_empty_headings(tmp_path: Path):
    spec = _make_complete_spec(constraints=[], data_sources=[])

    run_generator(spec, tmp_path)

    checkpoints = (tmp_path / "CHECKPOINTS.md").read_text(encoding="utf-8")
    assert "## Restricciones" not in checkpoints
    assert "## Fuentes de datos" not in checkpoints
    for agent in ("planner", "implementer", "reviewer"):
        assert "## restricciones" not in _agent_file(tmp_path, agent), agent


def test_feature_list_includes_a_task_per_audit_finding(tmp_path: Path):
    import json

    from src.models.harness_spec import AuditFinding

    spec = _make_complete_spec(
        audit_findings=[
            AuditFinding(
                check="no_git_remote",
                severity="blocking",
                description="El repositorio no tiene remoto.",
                suggested_fix="Configurar un remoto y hacer push.",
            ),
            AuditFinding(
                check="no_tests",
                severity="warning",
                description="No hay tests.",
                suggested_fix="Añadir cobertura mínima.",
            ),
        ]
    )

    run_generator(spec, tmp_path)

    tasks = json.loads((tmp_path / "feature_list.json").read_text(encoding="utf-8"))
    assert len(tasks) == 5

    blocking_task, warning_task = tasks[3], tasks[4]

    assert blocking_task["id"] == 4
    assert "El repositorio no tiene remoto." in blocking_task["title"]
    assert "Configurar un remoto y hacer push." in blocking_task["title"]
    assert blocking_task["priority"] == "high"
    assert blocking_task["complejidad"] == "media"
    assert blocking_task["depends_on"] == [1]

    assert warning_task["id"] == 5
    assert warning_task["priority"] == "medium"
    assert warning_task["complejidad"] == "baja"


def test_feature_list_has_three_tasks_without_audit_findings(tmp_path: Path):
    import json

    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    tasks = json.loads((tmp_path / "feature_list.json").read_text(encoding="utf-8"))
    assert len(tasks) == 3


def test_generator_produces_no_empty_files(tmp_path: Path):
    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    for path in tmp_path.rglob("*"):
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        assert content.strip(), f"file is empty: {path}"


def test_generator_leaves_no_unresolved_placeholders(tmp_path: Path):
    spec = _make_complete_spec()

    run_generator(spec, tmp_path)

    for path in tmp_path.rglob("*"):
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        assert content.count("{{") == content.count("}}"), (
            f"unbalanced placeholders in {path}"
        )


def test_generator_includes_tester_for_agent_project(tmp_path: Path):
    spec = _make_complete_spec(
        project_type="agent",
        agent_roles=[
            AgentRole(name="implementer", mode="BISTURÍ", scope="Implementa", tools=[]),
            AgentRole(name="reviewer", mode="FISCAL", scope="Revisa", tools=[]),
            AgentRole(name="tester", mode="QA", scope="Testea", tools=[]),
        ],
    )

    run_generator(spec, tmp_path)

    assert (tmp_path / ".claude" / "agents" / "tester.md").exists()

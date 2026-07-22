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

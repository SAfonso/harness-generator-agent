import subprocess
from pathlib import Path

from src.models.harness_spec import (
    AuditFinding,
    HarnessSpec,
    InferredField,
    InspectionResult,
    LLMConfig,
)
from src.tools.classify_project import classify_project

_MANIFEST_FILES = [
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
]

_STACK_BY_MANIFEST = {
    "package.json": "Node.js",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "pom.xml": "Java",
}

_DEPENDENCY_KEYWORDS = [
    "fastapi", "flask", "django", "react", "vue", "next", "svelte",
    "pyspark", "airflow", "pandas", "dbt", "kafka",
    "anthropic", "openai", "langchain", "langgraph",
    "click", "typer",
]

_TEST_DIR_NAMES = ["tests", "test", "spec", "__tests__"]
_TEST_FILE_PATTERNS = ["test_*.py", "*_test.py", "*.test.js", "*.spec.js", "*_spec.rb"]
_CI_PATHS = [".gitlab-ci.yml", ".circleci/config.yml"]


def inspect_project(path: Path) -> InspectionResult:
    if not path.is_dir():
        return InspectionResult(is_existing_project=False, fields={}, summary="")

    manifests = _read_manifests(path)
    has_git_history = _has_git_history(path)
    has_claude_md = _has_meaningful_content(path / "CLAUDE.md")
    has_docs = _has_meaningful_content(path / "README.md") or has_claude_md

    if not (manifests or has_git_history or has_docs):
        return InspectionResult(is_existing_project=False, fields={}, summary="")

    fields: dict[str, InferredField] = {}

    project_type_field = _infer_project_type(manifests)
    if project_type_field is not None:
        fields["project_type"] = project_type_field

    stack_field = _infer_stack(manifests)
    if stack_field is not None:
        fields["stack"] = stack_field

    findings = _audit_project(path, manifests, has_git_history, has_docs, has_claude_md)

    summary = _build_summary(path, manifests, has_git_history, has_docs, fields, findings)

    return InspectionResult(
        is_existing_project=True, fields=fields, findings=findings, summary=summary,
    )


def _read_manifests(path: Path) -> dict[str, str]:
    contents = {}
    for name in _MANIFEST_FILES:
        candidate = path / name
        if candidate.is_file():
            contents[name] = candidate.read_text(encoding="utf-8", errors="ignore")
    return contents


def _has_git_history(path: Path) -> bool:
    if not (path / ".git").is_dir():
        return False
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        capture_output=True,
    )
    return result.returncode == 0


def _has_meaningful_content(file: Path, min_length: int = 20) -> bool:
    if not file.is_file():
        return False
    return len(file.read_text(encoding="utf-8", errors="ignore").strip()) >= min_length


def _build_probe_spec(description: str) -> HarnessSpec:
    return HarnessSpec(
        project_type="other",
        description=description,
        stack=[],
        data_sources=[],
        constraints=[],
        acceptance_criteria=[],
        deliverable="",
        time_available="",
        mode="EJECUTOR",
        llm_config=LLMConfig(strategy="recommended"),
    )


def _infer_project_type(manifests: dict[str, str]) -> InferredField | None:
    if not manifests:
        return None

    guesses = {
        name: classify_project(_build_probe_spec(content))
        for name, content in manifests.items()
    }
    signal = {name: ptype for name, ptype in guesses.items() if ptype != "other"}

    if not signal:
        return None

    distinct = set(signal.values())
    if len(distinct) == 1:
        (ptype,) = distinct
        return InferredField(
            value=ptype,
            evidence=f"manifiesto(s): {', '.join(sorted(signal))}",
            confidence="high",
        )

    counts = {ptype: list(signal.values()).count(ptype) for ptype in distinct}
    best = max(distinct, key=lambda ptype: counts[ptype])
    evidence = "; ".join(f"{name} → {ptype}" for name, ptype in sorted(signal.items()))
    return InferredField(
        value=best,
        evidence=f"señales contradictorias entre manifiestos: {evidence}",
        confidence="low",
    )


def _infer_stack(manifests: dict[str, str]) -> InferredField | None:
    if not manifests:
        return None

    combined = " ".join(manifests.values()).lower()
    detected = {kw for kw in _DEPENDENCY_KEYWORDS if kw in combined}
    languages = {_STACK_BY_MANIFEST[name] for name in manifests}

    return InferredField(
        value=sorted(languages | detected),
        evidence=f"manifiesto(s): {', '.join(sorted(manifests))}",
        confidence="high",
    )


def _has_git_remote(path: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(path), "remote"],
        capture_output=True, text=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def _has_tests(path: Path) -> bool:
    if any((path / name).is_dir() for name in _TEST_DIR_NAMES):
        return True
    return any(any(path.rglob(pattern)) for pattern in _TEST_FILE_PATTERNS)


def _has_ci(path: Path) -> bool:
    workflows = path / ".github" / "workflows"
    if workflows.is_dir() and any(workflows.iterdir()):
        return True
    return any((path / ci_path).is_file() for ci_path in _CI_PATHS)


def _audit_project(
    path: Path,
    manifests: dict[str, str],
    has_git_history: bool,
    has_docs: bool,
    has_claude_md: bool,
) -> list[AuditFinding]:
    findings: list[AuditFinding] = []

    if not (path / ".git").is_dir():
        findings.append(AuditFinding(
            check="no_git_repo",
            severity="blocking",
            description="El proyecto no es un repositorio git.",
            suggested_fix="git init, primer commit y configurar un remoto — "
                           "NOTARIO no puede crear ramas ni PRs sin repo git.",
        ))
    elif not _has_git_remote(path):
        findings.append(AuditFinding(
            check="no_git_remote",
            severity="blocking",
            description="El repositorio git no tiene ningún remoto configurado.",
            suggested_fix="Configurar un remoto (ej. git remote add origin <url>) "
                           "y hacer push — NOTARIO no puede abrir PRs sin remoto.",
        ))

    if not _has_ci(path):
        findings.append(AuditFinding(
            check="no_ci",
            severity="warning",
            description="No hay configuración de CI (.github/workflows, .gitlab-ci.yml, .circleci).",
            suggested_fix="Añadir un pipeline de CI mínimo (lint + tests) — "
                           "CENTINELA no tiene nada que verificar antes de mergear sin él.",
        ))

    if not _has_tests(path):
        findings.append(AuditFinding(
            check="no_tests",
            severity="warning",
            description="No se ha encontrado ningún test existente en el proyecto.",
            suggested_fix="Añadir una cobertura mínima de tests sobre el flujo "
                           "principal antes de que FISCAL empiece a revisar cambios.",
        ))

    if not has_docs:
        findings.append(AuditFinding(
            check="empty_docs",
            severity="warning",
            description="Ni README.md ni CLAUDE.md tienen contenido documentado.",
            suggested_fix="Documentar el proyecto (README.md o CLAUDE.md) para que "
                           "el harness parta con contexto real, no de cero.",
        ))
    elif has_claude_md:
        findings.append(AuditFinding(
            check="existing_claude_md",
            severity="warning",
            description="Ya existe un CLAUDE.md con contenido en este proyecto.",
            suggested_fix="Revisar y fusionar a mano tu CLAUDE.md con el "
                           "harness/CLAUDE.md generado antes de sustituirlo — "
                           "revisa también tu README si documenta el flujo de "
                           "trabajo, el generador no lo toca ni lo genera.",
        ))

    if manifests:
        findings.append(AuditFinding(
            check="code_quality_review_pending",
            severity="warning",
            description="El código existente no ha sido auditado por calidad ni seguridad.",
            suggested_fix="Ejecutar /code-review (y /security-review si el proyecto "
                           "maneja datos sensibles) sobre el código existente antes "
                           "de seguir añadiendo funcionalidad.",
        ))

    return findings


def _build_summary(
    path: Path,
    manifests: dict[str, str],
    has_git_history: bool,
    has_docs: bool,
    fields: dict[str, InferredField],
    findings: list[AuditFinding],
) -> str:
    lines = [f"Proyecto ya empezado detectado en {path}."]
    if manifests:
        lines.append(f"Manifiestos encontrados: {', '.join(sorted(manifests))}.")
    if has_git_history:
        lines.append("Historial de git existente.")
    if has_docs:
        lines.append("README/CLAUDE.md con contenido.")
    if "project_type" in fields:
        field = fields["project_type"]
        lines.append(f"Tipo de proyecto inferido: {field.value} ({field.confidence}) — {field.evidence}.")
    if "stack" in fields:
        field = fields["stack"]
        lines.append(f"Stack inferido: {', '.join(field.value)} ({field.confidence}).")
    if not fields:
        lines.append("Sin señales suficientes para inferir tipo o stack — se preguntará en la entrevista.")
    if findings:
        resumen_hallazgos = "; ".join(f"{f.check} ({f.severity})" for f in findings)
        lines.append(f"Hallazgos de auditoría: {resumen_hallazgos}.")
    return " ".join(lines)


# TODO v2: inferir data_sources/constraints/acceptance_criteria/deliverable/
# time_available cuando exista evidencia explícita (CHECKPOINTS.md, feature_list.json
# de una ejecución previa del harness) — ver specs/tools.md#inspect_project

import subprocess
from pathlib import Path

from src.models.harness_spec import HarnessSpec, InferredField, InspectionResult, LLMConfig
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


def inspect_project(path: Path) -> InspectionResult:
    if not path.is_dir():
        return InspectionResult(is_existing_project=False, fields={}, summary="")

    manifests = _read_manifests(path)
    has_git_history = _has_git_history(path)
    has_docs = _has_meaningful_content(path / "README.md") or _has_meaningful_content(path / "CLAUDE.md")

    if not (manifests or has_git_history or has_docs):
        return InspectionResult(is_existing_project=False, fields={}, summary="")

    fields: dict[str, InferredField] = {}

    project_type_field = _infer_project_type(manifests)
    if project_type_field is not None:
        fields["project_type"] = project_type_field

    stack_field = _infer_stack(manifests)
    if stack_field is not None:
        fields["stack"] = stack_field

    summary = _build_summary(path, manifests, has_git_history, has_docs, fields)

    return InspectionResult(is_existing_project=True, fields=fields, summary=summary)


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


def _build_summary(
    path: Path,
    manifests: dict[str, str],
    has_git_history: bool,
    has_docs: bool,
    fields: dict[str, InferredField],
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
    return " ".join(lines)


# TODO v2: inferir data_sources/constraints/acceptance_criteria/deliverable/
# time_available cuando exista evidencia explícita (CHECKPOINTS.md, feature_list.json
# de una ejecución previa del harness) — ver specs/tools.md#inspect_project

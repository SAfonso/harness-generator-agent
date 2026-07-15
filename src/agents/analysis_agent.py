"""analysis_agent — decides harness structure from a partial HarnessSpec."""

import re

from src.config import AGENT_MODES, MIN_AGENTS_BY_TYPE
from src.models.harness_spec import AgentRole, HarnessSpec
from src.tools.classify_project import classify_project

_SCOPE_BY_NAME = {
    "leader":      "Orquesta la ejecución del harness y escala al usuario cuando toca",
    "planner":     "Descompone objetivos en tareas atómicas y asigna complejidad a cada una",
    "implementer": "Implementa las tareas del backlog",
    "reviewer":    "Revisa y valida el output contra los criterios de aceptación",
    "tester":      "Diseña y ejecuta tests para verificar el comportamiento",
}
_DEFAULT_SCOPE = "Rol especializado del harness"

_DAYS_RE = re.compile(r"(\d+)?\s*d[íi]as?")
_WEEKS_RE = re.compile(r"(\d+)?\s*semanas?")


def _detect_complexity(time_available: str) -> str:
    text = time_available.lower()
    if "hackathon" in text:
        return "simple"
    day_match = _DAYS_RE.search(text)
    if day_match:
        n = int(day_match.group(1)) if day_match.group(1) else 1
        if n <= 3:
            return "simple"
    week_match = _WEEKS_RE.search(text)
    if week_match:
        n = int(week_match.group(1)) if week_match.group(1) else 1
        if n <= 2:
            return "standard"
    return "standard"


def _build_agent_roles(project_type: str) -> list[AgentRole]:
    names = MIN_AGENTS_BY_TYPE.get(project_type, MIN_AGENTS_BY_TYPE["other"])
    return [
        AgentRole(
            name=name,
            mode=AGENT_MODES.get(name, "EJECUTOR"),
            scope=_SCOPE_BY_NAME.get(name, _DEFAULT_SCOPE),
            tools=[],
        )
        for name in names
    ]


_UNIVERSAL_RULES = [
    "Las tareas del backlog son atómicas: cortas, acotadas y con un único "
    "entregable verificable — nada de objetivos amplios tipo 'hazme el front'; "
    "esos los descompone el planner antes de entrar al backlog",
    "Cada tarea lleva complejidad (alta | media | baja) asignada por el planner, "
    "y se lanza con el modelo de su tier: alta → potente, media → intermedio, "
    "baja → económico",
]


def _build_rules(complexity: str) -> list[str]:
    if complexity == "simple":
        return _UNIVERSAL_RULES + [
            "Una tarea a la vez en in_progress",
            "Solo el reviewer puede marcar done",
            "Máximo 2 rechazos antes de escalar al usuario",
        ]
    return _UNIVERSAL_RULES + [
        "Una tarea a la vez en in_progress",
        "Solo el reviewer puede marcar done",
        "Máximo 3 rechazos antes de escalar al usuario",
        "El implementer no puede modificar el scope sin aprobación del leader",
        "Bitácora de errores obligatoria en progress/errors.md",
    ]


def run_analysis(spec: HarnessSpec) -> HarnessSpec:
    spec.project_type = classify_project(spec)
    spec.harness_complexity = _detect_complexity(spec.time_available)
    spec.agent_roles = _build_agent_roles(spec.project_type)
    spec.rules = _build_rules(spec.harness_complexity)
    return spec
